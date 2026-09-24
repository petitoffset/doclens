# Technical Decisions

This document records the established architectural choices for the DocLens MVP. Exact evaluation models and run results are recorded in the generated evaluation report rather than fixed as architecture.

## 1. MVP scope and implementation style

**Context:** DocLens is a technical interview exercise that must demonstrate a coherent RAG workflow without production-scale complexity.

**Decision:** Prefer simple, explicit application code and official SDKs. Do not add LangChain, provider abstractions, reranking, authentication, queues, deployment infrastructure, or other non-MVP features.

**Why it fits:** The important data flow and trade-offs remain visible and easy to explain.

**Trade-off:** The MVP deliberately lacks production capabilities and interchangeable infrastructure.

## 2. Application stack

**Context:** The project requires an API and a minimal browser interface.

**Decision:** Use Python 3.11 with FastAPI for the backend and a React, TypeScript, and Vite single-page frontend. Use `uv` and a committed lockfile for Python, and npm with a committed lockfile for the frontend.

**Why it fits:** Python supports the local ML workflow directly, while the small React application covers the complete demo without a broader frontend framework.

**Trade-off:** The project has separate backend and frontend runtimes and dependency sets.

## 3. Ingestion and local retrieval

**Context:** Bundled documents and user uploads need one searchable path while corpus processing remains local.

**Decision:** Accept `.md` and `.txt` documents through one validation, parsing, chunking, embedding, and indexing pipeline. Use 1,000-character chunks with 150-character overlap, local `sentence-transformers/all-MiniLM-L6-v2` embeddings, embedded persistent ChromaDB, and semantic top-three retrieval without reranking.

Technical sanitized filenames remain the source identity. A separate safe display filename preserves casing, spaces, and useful punctuation for the UI. Uploaded raw files are not retained after ingestion; only chunks, embeddings, and required metadata persist.

**Why it fits:** The shared, local pipeline is inspectable and requires no additional service.

**Trade-off:** Format support and retrieval sophistication are limited. Reprocessing requires another upload, source replacement is not failure-atomic, and renamed or removed bundled files can leave stale indexed chunks.

## 4. External LLM boundary and grounded answers

**Context:** Generation and LLM-based evaluation require an external model, but the corpus should remain local wherever possible.

**Decision:** Use OpenAI only for grounded generation and evaluation. Generation receives the question and at most three retrieved chunk texts—not the full corpus or internal source identifiers. Prompt instructions require answers from that context and abstention when it is insufficient. API source attribution comes directly from local retrieval metadata.

**Why it fits:** This provides useful answers and traceability while minimizing external data exposure and implementation complexity.

**Trade-off:** Retrieved content still leaves the local environment. Prompt-level grounding reduces risk but cannot guarantee completeness, faithfulness, or prompt-injection resistance.

## 5. Evaluation and security validation

**Context:** RAG quality and deterministic security behavior measure different concerns and should not be conflated.

**Decision:** Use a manually reviewed 12-question golden dataset for product quality. Measure document-level Hit@3, MRR@3, and Source Recall@3. Generate answers through the production path, then use a separately prompted judge call for binary correctness and faithfulness assessments with short rationales:

- Correctness compares the answer with the reference answer.
- Faithfulness compares the answer with retrieved context.

Generate `reports/eval.md` automatically with configuration, aggregate metrics, retrieved sources, answers, and judge rationales. Keep upload, filename, and query guardrails in deterministic tests; keep prompt-injection cases as separate demonstrations.

**Why it fits:** The metrics and per-case evidence are small enough to inspect manually, while security checks remain deterministic.

**Trade-off:** Retrieval metrics operate at document level and can count an irrelevant chunk from an expected document as a hit. LLM judging is model- and run-dependent, and a binary judgment can be sensitive to borderline wording.

## 6. Local data and observability

**Context:** The MVP needs persistent vectors and traceable behavior without committing generated data, sensitive content, or secrets.

**Decision:** Keep Chroma data local and excluded from Git. Emit structured JSON logs to stdout with request correlation and retrieval metadata, but without queries, answers, document content, API keys, or environment values. The application does not persist, rotate, or retain logs. Any committed example log must be manually sanitized from a real demo run.

**Why it fits:** The behavior is observable during development without adding logging infrastructure or sensitive local files.

**Trade-off:** There is no durable or centralized logging, retention policy, tracing backend, encryption layer, or multi-user isolation. The `generated` query outcome records that generation was invoked, not whether the model returned a substantive answer or abstained.

## Limitations and production considerations

The baseline shows that an expected source can appear in the top three while the answer-bearing chunk remains below the cutoff, and that multi-source retrieval can lack source diversity. It also shows that generation can omit or overstate a detail despite sufficient retrieved evidence. These are accepted MVP findings, not hidden by tuning after evaluation.

A production system would need requirements-driven work on access control, data governance, indexing reconciliation, failure-atomic updates, retrieval quality, evaluation stability, durable observability, operational resilience, and deployment architecture.
