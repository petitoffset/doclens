import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.evaluation import (
    JUDGE_INSTRUCTIONS,
    EvaluationError,
    EvaluationResult,
    GoldenCase,
    JudgeResult,
    OpenAIAnswerJudge,
    RetrievalScores,
    aggregate_retrieval,
    load_golden_cases,
    render_report,
    score_retrieval,
)
from app.retrieval import SearchResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def result(source_id: str, rank: int) -> SearchResult:
    return SearchResult(
        chunk_id=f"chunk-{rank}",
        text=f"Retrieved context {rank}",
        metadata={"source_id": source_id, "chunk_index": rank - 1},
        distance=rank / 10,
    )


def golden_case(*, expected_sources: tuple[str, ...] = ("a.md",)) -> GoldenCase:
    return GoldenCase(
        id="example",
        question="What is expected?",
        expected_sources=expected_sources,
        reference_answer="Expected answer.",
    )


def test_retrieval_metrics_use_source_documents_in_the_top_three() -> None:
    scores = score_retrieval(
        golden_case(expected_sources=("a.md", "b.md")),
        [result("unrelated.md", 1), result("b.md", 2), result("b.md", 3)],
    )

    assert scores == RetrievalScores(
        hit_at_3=1.0,
        mrr_at_3=0.5,
        source_recall_at_3=0.5,
    )


def test_retrieval_metrics_ignore_results_below_top_three() -> None:
    scores = score_retrieval(
        golden_case(),
        [
            result("x.md", 1),
            result("y.md", 2),
            result("z.md", 3),
            result("a.md", 4),
        ],
    )

    assert scores == RetrievalScores(0.0, 0.0, 0.0)


def test_aggregate_retrieval_uses_macro_averages() -> None:
    case = golden_case()
    evaluations = [
        EvaluationResult(case, (), RetrievalScores(1.0, 1.0, 1.0)),
        EvaluationResult(case, (), RetrievalScores(0.0, 0.5, 0.0)),
    ]

    assert aggregate_retrieval(evaluations) == RetrievalScores(0.5, 0.75, 0.5)


def test_load_golden_cases_validates_sources_and_duplicate_ids(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "known.md").write_text("Known", encoding="utf-8")
    dataset = tmp_path / "golden.json"
    dataset.write_text(
        json.dumps(
            {
                "version": 1,
                "cases": [
                    {
                        "id": "duplicate",
                        "question": "First?",
                        "expected_sources": ["known.md"],
                        "reference_answer": "First.",
                    },
                    {
                        "id": "duplicate",
                        "question": "Second?",
                        "expected_sources": ["missing.md"],
                        "reference_answer": "Second.",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(EvaluationError, match="Duplicate golden case id"):
        load_golden_cases(dataset, corpus_dir=corpus)


def test_project_golden_dataset_is_valid() -> None:
    cases = load_golden_cases(
        PROJECT_ROOT / "evaluation" / "golden.json",
        corpus_dir=PROJECT_ROOT / "corpus",
    )

    assert len(cases) == 12
    assert "ingestion-api-429-recovery" in {case.id for case in cases}


class FakeResponses:
    def __init__(self, output: dict[str, Any]) -> None:
        self.output = output
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps(self.output))


def test_judge_keeps_correctness_and_faithfulness_inputs_explicit() -> None:
    responses = FakeResponses(
        {
            "correctness": {"pass": True, "reason": "Matches reference."},
            "faithfulness": {"pass": False, "reason": "Unsupported detail."},
        }
    )
    judge = OpenAIAnswerJudge(
        model="judge-model",
        client=SimpleNamespace(responses=responses),
    )
    retrieved = [result("a.md", 1)]

    judgement = judge.judge(golden_case(), "Generated answer.", retrieved)

    assert judgement == JudgeResult(
        correctness=True,
        correctness_reason="Matches reference.",
        faithfulness=False,
        faithfulness_reason="Unsupported detail.",
    )
    call = responses.calls[0]
    assert call["instructions"] == JUDGE_INSTRUCTIONS
    payload = json.loads(call["input"])
    assert payload["reference_answer"] == "Expected answer."
    assert payload["retrieved_context"] == ["Retrieved context 1"]
    assert payload["generated_answer"] == "Generated answer."


def test_report_contains_actual_retrieval_and_generation_results() -> None:
    case = golden_case()
    evaluation = EvaluationResult(
        case=case,
        retrieved=(result("a.md", 1),),
        retrieval_scores=RetrievalScores(1.0, 1.0, 1.0),
        answer="Generated answer.",
        judge=JudgeResult(True, "Correct.", True, "Supported."),
    )

    report = render_report(
        [evaluation],
        embedding_model="embedding-model",
        generation_model="generation-model",
        judge_model="judge-model",
        generated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert "| Hit@3 | 100.0% |" in report
    assert "| Correctness | 100.0% |" in report
    assert "**Reference answer:** Expected answer." in report
    assert "**Correctness:** Pass — Correct." in report
    assert "**Faithfulness:** Pass — Supported." in report
    assert "Generated: 2026-01-02T00:00:00+00:00" in report
