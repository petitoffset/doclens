# DocLens

DocLens is a lightweight retrieval-augmented generation (RAG) assistant for searching internal documents and answering questions with traceable sources. It is a focused MVP technical interview project for PALO IT Labs, not a production-complete system.

## What it demonstrates

- Indexing a bundled synthetic PulseBoard corpus
- Uploading `.md` and `.txt` documents through the same ingestion pipeline
- Local chunking, Sentence Transformer embeddings, and persistent ChromaDB retrieval
- Grounded OpenAI answer generation from the top three retrieved chunks
- Source attribution, deterministic guardrail tests, and structured JSON observability
- Offline retrieval and answer-quality evaluation with an automatically generated report
- A minimal React interface for the complete demo flow

## Architecture

Documents are validated, decoded, split into overlapping character chunks, embedded locally with `sentence-transformers/all-MiniLM-L6-v2`, and stored in an embedded ChromaDB collection. A question uses the same embedding model to retrieve the top three chunks. Only the question and those chunk texts are sent to OpenAI for grounded answer generation; source metadata remains local and is returned separately by the API.

The FastAPI backend exposes:

| Endpoint | Purpose |
| --- | --- |
| `POST /api/corpus/index` | Index the bundled Markdown corpus |
| `POST /api/documents/upload` | Validate and index one `.md` or `.txt` upload |
| `POST /api/query` | Retrieve context and generate a sourced answer |

The React/Vite frontend calls these endpoints through its local development proxy.

## Run locally

Requirements:

- Python 3.11
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm
- An OpenAI API key and generation model

### Backend

From the repository root in PowerShell:

```powershell
cd backend
uv sync
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_MODEL = "your-generation-model"
uv run uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Configuration is read from process environment variables; `.env.example` documents the required names but the application does not load `.env` files automatically.

### Frontend

In a second PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:4173`. The host and port are defined in `frontend/vite.config.ts`, and `/api` is proxied to the FastAPI server on port 8000.

For a short demo:

1. Index the bundled PulseBoard corpus.
2. Optionally upload a Markdown or text document.
3. Ask a question.
4. Inspect the answer and unique source documents.

## Validation

Backend tests:

```powershell
cd backend
$env:PYTHONPATH = "."
uv run pytest
```

Frontend checks:

```powershell
cd frontend
npm test
npm run typecheck
npm run build
```

Automated tests mock external OpenAI calls and do not require a real API key.

## Evaluation

The manually reviewed golden dataset contains 12 single-source and multi-source product questions. Retrieval is measured with Hit@3, MRR@3, and Source Recall@3. A separate OpenAI judge evaluates:

- **Correctness:** generated answer compared with the reference answer
- **Faithfulness:** generated answer compared with the retrieved context

To regenerate the report from `backend/`:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_MODEL = "your-generation-model"
$env:OPENAI_JUDGE_MODEL = "your-judge-model"
uv run python -m scripts.run_evaluation
```

This command uses the production ingestion and retrieval path, performs external generation and judging calls, and overwrites [`reports/eval.md`](reports/eval.md). It can incur API usage. Judge results are model- and run-dependent, so the per-case rationales should be reviewed alongside aggregate scores.

The final MVP baseline used `gpt-6-luna` for generation and `gpt-6-sol` for judging:

| Metric | Result |
| --- | ---: |
| Hit@3 | 100.0% |
| MRR@3 | 77.8% |
| Source Recall@3 | 95.8% |
| Correctness | 75.0% |
| Faithfulness | 91.7% |

Security validation remains separate from this quality dataset: deterministic backend tests cover upload and query guardrails, while prompt-injection resilience is demonstrated by `backend/scripts/demo_prompt_injection.py`.

## Data handling and observability

- Uploaded source files are processed in memory and are not retained as raw copies.
- Indexed chunks, embeddings, and required source metadata persist in local ChromaDB data excluded from Git.
- Technical filenames and source IDs are sanitized; a separate safe display filename preserves useful user-facing formatting.
- The external generation call receives only the question and retrieved chunk text, not the full corpus or internal source identifiers.
- Structured application logs are emitted as one JSON object per line to stdout. The application does not persist, rotate, or retain logs.
- Logs exclude query text, answer text, retrieved content, uploaded content, secrets, and environment values.
- A sanitized example captured from a real local demo is available at [`logs/example.jsonl`](logs/example.jsonl).

## Known limitations and production next steps

- Retrieval is fixed at top three without reranking. A source-document hit can still retrieve the wrong chunk, as the 429 evaluation case demonstrates.
- Multi-source questions may miss an expected document or use multiple top-three positions for chunks from one source.
- The accepted-events evaluation case retrieved sufficient evidence, but generation omitted the cache delay and overstated immediate visibility after manual refresh.
- The CSV support-ticket result is borderline and judge-sensitive: the answer supplied the corrective steps but did not explicitly restate that uploading the corrected file succeeded.
- In query logs, `outcome="generated"` means retrieval returned context and generation was invoked; the generated response may still be an insufficient-context abstention.
- Prompt-level grounding and demonstrations do not provide comprehensive prompt-injection protection.
- The local index has no authentication or multi-user isolation, and source replacement is not failure-atomic. Removing or renaming a bundled source can leave stale chunks until the index is rebuilt.
- Production use would require explicit access control, data governance, durable observability, operational recovery, and retrieval-quality work based on real data.
