"""Run the DocLens golden evaluation and write reports/eval.md."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from app.evaluation import (
    EvaluationResult,
    OpenAIAnswerJudge,
    load_golden_cases,
    render_report,
    score_retrieval,
)
from app.generation import OpenAIAnswerGenerator
from app.ingestion import DEFAULT_CORPUS_DIR
from app.retrieval import (
    DEFAULT_EMBEDDING_MODEL,
    PersistentRetriever,
    index_bundled_corpus,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN_PATH = PROJECT_ROOT / "evaluation" / "golden.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "eval.md"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Skip external answer generation and LLM judging.",
    )
    args = parser.parse_args()

    cases = load_golden_cases(args.golden, corpus_dir=DEFAULT_CORPUS_DIR)
    generator = None
    judge = None
    if not args.retrieval_only:
        generator = OpenAIAnswerGenerator.from_environment()
        judge = OpenAIAnswerJudge.from_environment()

    with TemporaryDirectory(
        prefix="doclens-evaluation-",
        ignore_cleanup_errors=True,
    ) as temporary_directory:
        retriever = PersistentRetriever(
            persist_directory=Path(temporary_directory) / "chroma",
            collection_name="doclens_evaluation",
        )
        indexed_count = index_bundled_corpus(retriever)
        print(f"Indexed {indexed_count} chunks for evaluation.")

        results: list[EvaluationResult] = []
        for position, case in enumerate(cases, start=1):
            retrieved = tuple(retriever.search(case.question))
            answer = generator.generate(case.question, retrieved) if generator else None
            judgement = judge.judge(case, answer, retrieved) if judge and answer else None
            results.append(
                EvaluationResult(
                    case=case,
                    retrieved=retrieved,
                    retrieval_scores=score_retrieval(case, retrieved),
                    answer=answer,
                    judge=judgement,
                )
            )
            print(f"Evaluated {position}/{len(cases)}: {case.id}")

    report = render_report(
        results,
        embedding_model=DEFAULT_EMBEDDING_MODEL,
        generation_model=os.getenv("OPENAI_MODEL") if generator else None,
        judge_model=judge.model if judge else None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote evaluation report to {args.output}")


if __name__ == "__main__":
    main()
