# DocLens

DocLens indexes internal Markdown and text documents, retrieves relevant passages locally, and uses grounded LLM generation to answer questions with traceable sources. It is a focused RAG MVP built to keep the full data flow easy to inspect and defend.

## Stack

| Area | Technology |
| --- | --- |
| API | Python 3.11, FastAPI |
| Frontend | React, TypeScript, Vite |
| Retrieval | Sentence Transformers, persistent embedded ChromaDB |
| Generation and judging | OpenAI Responses API |
| Tooling | uv, npm, pytest, Vitest |

## Architecture

```text
Bundled Markdown or .md/.txt upload
  -> validate and decode -> chunk -> local embedding -> persistent ChromaDB

Question
  -> local embedding -> top-3 semantic retrieval -> grounded OpenAI generation
  -> answer + local source metadata -> FastAPI -> React
```

The backend exposes three operations: index the bundled corpus, upload a document, and query the index. During runtime answer generation, only the question and top-three chunk text are sent to OpenAI; source and chunk identifiers remain local. See [Technical decisions](DECISIONS.md) for rationale and trade-offs.

## Quick start

```powershell
# First-time setup
Copy-Item .env.example .env
# Fill in OPENAI_API_KEY and OPENAI_MODEL in .env
cd backend
uv sync
cd ../frontend
npm install

# Start backend (from backend/)
cd ../backend
uv run uvicorn app.main:app --reload

# In another terminal, start frontend
cd frontend
npm run dev

# Open
# http://127.0.0.1:4173
```

## Commands

Run these from the indicated directory.

### Backend tests

```powershell
cd backend
uv run python -m pytest
```

### Frontend validation

```powershell
cd frontend
npm test
npm run typecheck
npm run build
```

### Evaluation

```powershell
cd backend
uv run python -m scripts.run_evaluation
```

The full run uses external generation and judge calls and overwrites [`reports/eval.md`](reports/eval.md). See the [evaluation guide](evaluation/README.md) for retrieval-only mode, metric definitions, and limitations.

### Prompt-injection demonstration

```powershell
cd backend
uv run python -m scripts.demo_prompt_injection
```

This is a qualitative live-model demonstration, separate from the automated quality evaluation.

## Evaluation snapshot

The committed 12-case baseline used `gpt-6-luna` for generation and `gpt-6-sol` for judging.

| Retrieval | Result | Generation | Result |
| --- | ---: | --- | ---: |
| Hit@3 | 100.0% | Correctness | 75.0% |
| MRR@3 | 77.8% | Faithfulness | 91.7% |
| Source Recall@3 | 95.8% |  |  |

These results include known retrieval and generation failures. Review the [evaluation methodology](evaluation/README.md) and [generated report](reports/eval.md) rather than treating the aggregate scores as a production-quality claim.

## Repository guide

| Path | Purpose |
| --- | --- |
| [`backend/app/`](backend/app/) | Ingestion, retrieval, generation, API, evaluation, and observability |
| [`frontend/src/`](frontend/src/) | Minimal document and question-answering interface |
| [`corpus/`](corpus/) | Synthetic PulseBoard source documents and non-indexed fact ledger |
| [`evaluation/`](evaluation/) | Golden dataset and evaluation documentation |
| [`reports/eval.md`](reports/eval.md) | Generated baseline with per-case evidence |
| [`logs/example.jsonl`](logs/example.jsonl) | Sanitized structured events from a real local demo |
| [`DECISIONS.md`](DECISIONS.md) | Architectural decisions, alternatives, and consequences |
| [`PLAN.md`](PLAN.md) | Completed milestone history and explicit MVP scope |

## MVP boundaries

DocLens deliberately omits authentication, multi-user isolation, reranking, provider abstraction, background jobs, deployment infrastructure, and comprehensive automated prompt-injection benchmarking. Uploaded raw files are not retained; local Chroma data is ignored by Git; application logs go to stdout and are not persisted by the application.

See [Technical decisions](DECISIONS.md) for the security, data, observability, and production trade-offs.
