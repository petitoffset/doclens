# DocLens Technical Decisions

This is a lightweight architectural decision record for the completed DocLens MVP. The decisions remain together because the system is small; [`PLAN.md`](PLAN.md) preserves delivery history, while the generated [`reports/eval.md`](reports/eval.md) preserves measured results.

All decisions below are **accepted for the MVP**. Production use would require revisiting them against real users, data sensitivity, scale, and operating constraints.

## Decision index

| ID | Decision | Primary evidence |
| --- | --- | --- |
| [DL-001](#dl-001--focused-mvp-with-explicit-code) | Focused MVP with explicit code | [`PLAN.md`](PLAN.md), repository structure |
| [DL-002](#dl-002--python-api-and-react-client) | Python API and React client | [`backend/pyproject.toml`](backend/pyproject.toml), [`frontend/package.json`](frontend/package.json) |
| [DL-003](#dl-003--shared-local-ingestion-and-retrieval) | Shared local ingestion and retrieval | [`backend/app/ingestion.py`](backend/app/ingestion.py), [`backend/app/retrieval.py`](backend/app/retrieval.py) |
| [DL-004](#dl-004--narrow-external-llm-boundary) | Narrow external LLM boundary | [`backend/app/generation.py`](backend/app/generation.py), [`backend/tests/test_prompt_guardrails.py`](backend/tests/test_prompt_guardrails.py) |
| [DL-005](#dl-005--quality-evaluation-separate-from-security-validation) | Quality evaluation separate from security validation | [`evaluation/golden.json`](evaluation/golden.json), [`reports/eval.md`](reports/eval.md) |
| [DL-006](#dl-006--minimal-structured-observability) | Minimal structured observability | [`backend/app/observability.py`](backend/app/observability.py), [`logs/example.jsonl`](logs/example.jsonl) |

## DL-001 — Focused MVP with explicit code

**Context.** The assignment needs a coherent, defensible RAG workflow, not a production platform. Extra abstraction would make the important data flow harder to inspect within the exercise.

**Decision.** Keep application code direct and use official or focused libraries. Do not introduce LangChain, provider abstractions, authentication, queues, deployment infrastructure, or other unapproved production features.

**Rationale.** The repository exposes the ingestion, retrieval, generation, and evaluation boundaries directly, making their behavior and trade-offs easier to test and explain.

**Alternatives considered.** LangChain and a multi-provider layer were deliberately deferred because the MVP has one concrete workflow and one external provider. Authentication, background processing, and deployment infrastructure were also excluded until requirements justify them.

**Consequences.** The code is small and legible, but the system is not provider-portable or production-ready. The completed scope and exclusions are recorded in [`PLAN.md`](PLAN.md).

## DL-002 — Python API and React client

**Context.** DocLens needs local ML integration, an HTTP API, and a minimal browser demo.

**Decision.** Use Python 3.11 and FastAPI for the backend, with dependencies managed by `uv` and a committed lockfile. Use React, TypeScript, and Vite for the single-page client, with npm and a committed lockfile.

**Rationale.** Python supports Sentence Transformers and ChromaDB directly. React provides the required interactive flow without expanding the backend into UI concerns; TypeScript and the production build add lightweight client-side verification.

**Alternatives considered.** The stack was an established project direction, so a broad framework comparison was not warranted. Deployment infrastructure was deliberately deferred under the MVP scope.

**Consequences.** Backend and frontend have separate runtimes and dependency sets. Vite handles local API proxying; no production hosting or deployment topology is defined.

## DL-003 — Shared local ingestion and retrieval

**Context.** Bundled documents and uploads must behave consistently, remain locally searchable across restarts, and avoid additional services.

**Decision.** Route bundled Markdown and uploaded `.md`/`.txt` files through the same validation, decoding, chunking, embedding, and indexing path. Use 1,000-character chunks with 150-character overlap, local `sentence-transformers/all-MiniLM-L6-v2` embeddings, embedded persistent ChromaDB, and semantic top-three retrieval without reranking.

Technical sanitized filenames remain the source identity. A separate safe display filename preserves useful human formatting. Uploaded raw files are not retained after ingestion; only chunks, embeddings, and required metadata persist.

**Rationale.** A shared path prevents corpus and upload behavior from drifting. Local embeddings and embedded persistence keep the data flow inspectable and require no Chroma server.

**Alternatives considered.** A purely ephemeral index was rejected because local persistence is useful for repeat demos. A fixed corpus directory alone was rejected in favor of manual uploads. A Chroma server, retained raw-upload store, reranker, and more elaborate indexing infrastructure were deliberately deferred.

**Consequences.** Format support and retrieval sophistication are limited. Reprocessing requires another upload, replacement is not failure-atomic, and renamed or removed bundled files can leave stale chunks. The [baseline report](reports/eval.md) also shows that document-level top-three success does not guarantee retrieval of the answer-bearing chunk.

## DL-004 — Narrow external LLM boundary

**Context.** Grounded answers and LLM-based evaluation need an external model, while the corpus and retrieval metadata should remain local wherever possible.

**Decision.** Use OpenAI only for grounded generation and evaluation. The generation request contains the question and at most three retrieved chunk texts—not the full corpus or internal source and chunk IDs. Prompt instructions require use of provided context and abstention when it is insufficient. API source attribution comes directly from retrieval metadata.

**Rationale.** The boundary minimizes external data exposure, keeps citations deterministic, and avoids conflating model output with source identity.

**Alternatives considered.** Multiple model providers and a provider abstraction were deferred. A calibrated retrieval-score abstention threshold was not introduced without evaluation evidence. A separate citation-validation subsystem was rejected because retrieved metadata already supplies traceability for the MVP.

**Consequences.** Retrieved content and the user question still leave the local environment. Prompt-level grounding cannot guarantee completeness, faithfulness, or prompt-injection resistance. The [evaluation report](reports/eval.md) retains both successful and failed examples rather than hiding those limitations.

## DL-005 — Quality evaluation separate from security validation

**Context.** RAG quality, deterministic input controls, and prompt-injection behavior answer different questions and should not be collapsed into one score.

**Decision.** Use a manually reviewed 12-question product-quality dataset. Measure document-level Hit@3, MRR@3, and Source Recall@3. Generate answers through the production path, then use a separately prompted judge for binary correctness and faithfulness with short rationales:

- Correctness compares the generated answer with the reference answer.
- Faithfulness compares the generated answer with retrieved context.

Generate [`reports/eval.md`](reports/eval.md) automatically with run configuration, per-case retrieval, answers, judgments, and aggregate metrics. Keep file, filename, upload-size, and query-length controls in deterministic tests. Keep prompt-injection cases in a separate manual demonstration.

**Rationale.** Retrieval failures remain distinguishable from generation failures, while deterministic security behavior stays repeatable and independent of an LLM judge.

**Alternatives considered.** Security cases were intentionally excluded from the golden quality dataset. A comprehensive automated prompt-injection benchmark and more elaborate evaluation platform were deferred as disproportionate to this corpus and MVP.

**Consequences.** Document-level retrieval metrics can count an irrelevant chunk from an expected document as a hit. Binary LLM judgments are model- and run-dependent and can be sensitive to borderline wording. The baseline therefore includes per-case evidence and reports 75.0% correctness and 91.7% faithfulness alongside 100.0% Hit@3, rather than reducing quality to one headline number.

## DL-006 — Minimal structured observability

**Context.** A local demo needs request correlation and retrieval traceability without logging sensitive content or adding an operational logging stack.

**Decision.** Emit one structured JSON event per line to stdout. Request events include method, path, status, duration, and request ID; query events add retrieved source IDs, chunk IDs, and distances. Exclude queries, answers, retrieved and uploaded content, API keys, and environment values. The application does not persist, rotate, or retain logs. Chroma data remains local and excluded from Git.

**Rationale.** This provides enough evidence to debug and demonstrate the request/retrieval flow while keeping the implementation and data policy explicit.

**Alternatives considered.** File logging, centralized collection, tracing infrastructure, and application-managed retention were deliberately deferred. The committed [`logs/example.jsonl`](logs/example.jsonl) is a manually sanitized capture from a real run, not application-managed persistence.

**Consequences.** Logs disappear unless the process output is captured externally. The `generated` query outcome means retrieval returned context and generation was invoked; it does not prove that the model produced a substantive answer rather than an abstention. There is no durable audit trail, centralized search, rotation, retention enforcement, or cross-service tracing.

## Production reconsiderations

These decisions optimize for a small, reviewable local system. Production planning should begin with concrete requirements, then revisit access control and data governance, tenant isolation, index reconciliation and atomic updates, retrieval quality, evaluation stability, durable observability, operational recovery, and deployment architecture. None of those capabilities should be inferred from this MVP.
