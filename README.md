# DocLens

DocLens is a lightweight retrieval-augmented generation (RAG) assistant for searching internal documents and answering questions with traceable sources. It is a focused technical-interview MVP for PALO IT Labs, designed to make the complete RAG path—and its limitations—easy to inspect and explain.

## Start here

| Document or artifact | What it shows |
| --- | --- |
| [`DECISIONS.md`](DECISIONS.md) | Architectural choices, alternatives, and consequences |
| [`PLAN.md`](PLAN.md) | The five completed implementation milestones and deliberately excluded scope |
| [`reports/eval.md`](reports/eval.md) | Generated per-question evidence and final quality baseline |
| [`evaluation/golden.json`](evaluation/golden.json) | The manually reviewed evaluation questions, reference answers, and expected sources |
| [`logs/example.jsonl`](logs/example.jsonl) | Sanitized structured events captured during a real local demo |
| [`corpus/fact-ledger.yaml`](corpus/fact-ledger.yaml) | Canonical facts used to keep the synthetic PulseBoard corpus consistent; not indexed |

## System at a glance

The implemented flow is intentionally small:

```text
Bundled Markdown or .md/.txt upload
  -> validate and decode -> chunk -> local embedding -> persistent ChromaDB

Question
  -> local embedding -> top-3 semantic retrieval -> grounded OpenAI generation
  -> answer + source metadata returned by FastAPI -> rendered by React
```

The backend uses Python 3.11 and FastAPI. It splits documents into overlapping character chunks, embeds them with `sentence-transformers/all-MiniLM-L6-v2`, and stores chunks, embeddings, and source metadata in embedded ChromaDB. The React/TypeScript/Vite frontend provides corpus indexing, document upload, question submission, and sourced answer rendering.

Only the question and the text of the top three retrieved chunks cross the external generation boundary. The full corpus, source IDs, chunk IDs, and other retrieval metadata remain local. See [DL-003](DECISIONS.md#dl-003--shared-local-ingestion-and-retrieval) and [DL-004](DECISIONS.md#dl-004--narrow-external-llm-boundary) for the rationale and consequences.

### API surface

| Endpoint | Purpose |
| --- | --- |
| `POST /api/corpus/index` | Index the bundled Markdown corpus |
| `POST /api/documents/upload` | Validate and index one `.md` or `.txt` upload |
| `POST /api/query` | Retrieve context and generate a sourced answer |

## Run and demo locally

Requirements:

- Python 3.11 and [uv](https://docs.astral.sh/uv/)
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

The API runs at `http://127.0.0.1:8000`. Configuration is read from process environment variables. [`.env.example`](.env.example) documents the names, but the application does not load `.env` files automatically.

### Frontend

In a second PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:4173`. Vite binds to that address and proxies `/api` to FastAPI on port 8000.

For a short end-to-end demo:

1. Index the bundled PulseBoard corpus.
2. Ask a grounded product question and inspect its sources.
3. Upload a Markdown or text document, then query facts from it.
4. Try an unsupported upload to demonstrate deterministic validation.

## Validate the implementation

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

Automated tests mock the OpenAI call boundary and require no real API key. They exercise real application routing, ingestion and retrieval behavior where appropriate, plus deterministic upload, query, and prompt-boundary guardrails. The two live prompt-injection scenarios remain a separate manual demonstration in [`backend/scripts/demo_prompt_injection.py`](backend/scripts/demo_prompt_injection.py).

## Evaluation evidence

The 12-case golden dataset covers single-source and multi-source product questions. Retrieval and generation are evaluated separately:

- **Hit@3:** whether any expected source document appears in the top three
- **MRR@3:** how highly the first expected source ranks
- **Source Recall@3:** the fraction of expected documents represented in the top three
- **Correctness:** the generated answer compared with the reference answer
- **Faithfulness:** the generated answer compared with retrieved context

To regenerate the report from `backend/`:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_MODEL = "your-generation-model"
$env:OPENAI_JUDGE_MODEL = "your-judge-model"
uv run python -m scripts.run_evaluation
```

The command uses the production ingestion, retrieval, and generation path, makes external generation and judge calls, and overwrites [`reports/eval.md`](reports/eval.md). It can incur API usage. Judge results are model- and run-dependent, so the generated answers and per-case rationales remain part of the evidence—not just the aggregate scores.

The final MVP baseline used `gpt-6-luna` for generation and `gpt-6-sol` for judging:

| Metric | Result |
| --- | ---: |
| Hit@3 | 100.0% |
| MRR@3 | 77.8% |
| Source Recall@3 | 95.8% |
| Correctness | 75.0% |
| Faithfulness | 91.7% |

These numbers are deliberately not presented as a production quality claim. The [full report](reports/eval.md) shows three correctness failures and one faithfulness failure. In particular:

- The 429 case counted as a document-level retrieval hit, but the answer-bearing chunk was outside the top-three context and the model abstained.
- One multi-source case retrieved only one of its two expected documents, exposing limited source diversity.
- The accepted-events case retrieved sufficient evidence, but generation omitted the cache delay and overstated immediate visibility after manual refresh.
- The CSV support-ticket result is borderline and judge-sensitive: the answer gave the corrective steps but did not explicitly state that uploading the corrected file succeeded.

The evaluation design and its known measurement limitations are recorded in [DL-005](DECISIONS.md#dl-005--quality-evaluation-separate-from-security-validation).

## Data, security, and observability boundaries

- Uploaded source files are processed in memory and are not retained as raw copies.
- Indexed chunks, embeddings, and required metadata persist in local ChromaDB data excluded from Git.
- Technical filenames and source IDs are sanitized; a separate safe display filename preserves useful user-facing formatting.
- Source attribution comes from local retrieval metadata rather than model-generated citations.
- Structured events are emitted as one JSON object per line to stdout. The application does not persist, rotate, or retain logs.
- Logs exclude query text, answer text, retrieved content, uploaded content, secrets, and environment values.
- In query logs, `outcome="generated"` means retrieval returned context and generation was invoked; the response may still be an insufficient-context abstention.

The committed [example log](logs/example.jsonl) was sanitized from a real demo and demonstrates request correlation, retrieval metadata, successful indexing and upload, query flows, and a rejected upload. Deterministic security tests and quality evaluation remain separate by design; see [DL-005](DECISIONS.md#dl-005--quality-evaluation-separate-from-security-validation) and [DL-006](DECISIONS.md#dl-006--minimal-structured-observability).

## MVP boundary and next steps

DocLens intentionally stops short of production infrastructure. It has no authentication, multi-user isolation, chat history, provider abstraction, reranking, background jobs, deployment system, or comprehensive automated prompt-injection benchmark. [`PLAN.md`](PLAN.md) is the completed delivery roadmap and authoritative out-of-scope list.

The most important known engineering limitations are:

- Fixed top-three retrieval can select the expected document but the wrong chunk, and can spend multiple positions on one source.
- Prompt-level grounding improves behavior but does not guarantee completeness, faithfulness, or prompt-injection resistance.
- Replacing an indexed source is not failure-atomic; removing or renaming bundled sources can leave stale chunks until the index is rebuilt.
- Logs are useful during a local run but are not durable or centrally collected.

Production work should start from demonstrated requirements and the evidence above: access control and data governance, index reconciliation and atomic updates, retrieval-quality improvements, durable observability, operational recovery, and deployment architecture. The project deliberately does not pre-build those systems for an interview MVP.
