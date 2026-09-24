# Technical Decisions

This document records established architectural choices for the DocLens MVP. Exact model names, chunking parameters, limits, schemas, and other implementation details will be selected during implementation.

## 1. MVP scope and implementation style

**Context:** DocLens is a technical interview exercise that must demonstrate a coherent RAG workflow without production-scale complexity.

**Decision:** Prefer simple, explicit application code and official SDKs. Do not add LangChain, provider abstractions, reranking, authentication, queues, deployment infrastructure, or other non-MVP features without approval.

**Why it fits:** The important data flow and trade-offs remain visible and easy to explain.

**Trade-off:** The MVP deliberately lacks production capabilities and interchangeable infrastructure.

## 2. Application stack

**Context:** The project requires an API and a minimal browser interface.

**Decision:** Use Python with FastAPI for the backend and React for a single-page frontend.

**Why it fits:** Python supports the local ML workflow directly, while React is sufficient for the small interactive UI.

**Trade-off:** The project has separate backend and frontend runtimes and dependency sets.

## 3. Ingestion and local retrieval

**Context:** Both bundled demonstration documents and user uploads must use the same searchable index while keeping corpus processing local.

**Decision:** Accept `.md` and `.txt` documents through one validation, parsing, chunking, embedding, and indexing pipeline. Generate embeddings locally with Sentence Transformers, persist indexed chunks, embeddings, and required source metadata in embedded ChromaDB, and use semantic top-3 retrieval without reranking. Uploaded source files are not retained as separate raw copies after ingestion.

**Why it fits:** A shared pipeline avoids inconsistent behavior, and local persistent retrieval provides a complete workflow without an additional service.

**Trade-off:** Format support and retrieval sophistication are intentionally limited. Reprocessing an upload from its original form requires the user to upload it again.

## 4. External LLM boundary and grounded answers

**Context:** Answer generation and LLM-based evaluation require an external model, but the document corpus should remain local wherever possible.

**Decision:** Use the OpenAI API only for grounded answer generation and evaluation. Send only the user question and retrieved context, never the full corpus. Instruct the model to answer from that context and state when it is insufficient. Return sources directly from retrieved-chunk metadata rather than using a separate citation-validation subsystem.

**Why it fits:** This provides useful answers and traceability while minimizing external data exposure and implementation complexity.

**Trade-off:** Retrieved content still leaves the local environment. Prompt-level grounding and abstention reduce risk but do not guarantee faithful behavior.

## 5. Evaluation and security validation

**Context:** RAG quality and deterministic security behavior measure different concerns and should not be conflated.

**Decision:** Evaluate retrieval and answer quality with a small manually verifiable golden dataset. Report Hit@3, MRR@3, and Source Recall@3 for retrieval, plus correctness and faithfulness from a separate LLM judge. Validate file types, upload size, query length, and filename handling with deterministic backend tests. Demonstrate prompt-injection resilience with one or two adversarial scenarios rather than a separate benchmark.

**Why it fits:** The quality metrics remain interpretable, while guardrails can be tested reliably and independently.

**Trade-off:** LLM-judge results are nondeterministic, and the prompt-injection demonstrations do not establish comprehensive security.

## 6. Local data and observability

**Context:** The MVP needs persistent vectors and traceable runtime behavior without committing generated data, sensitive content, or secrets.

**Decision:** Keep Chroma data and runtime logs local and excluded from Git. Use structured JSON logs without API keys or raw document content, and commit only sanitized example logs.

**Why it fits:** This supports debugging and demonstration with a small, explicit data policy.

**Trade-off:** The MVP provides no centralized logging, automated retention, encryption, or multi-user isolation.

## Limitations and production considerations

These choices optimize for a focused local demonstration. A production system would need to revisit access control, data governance, observability, retrieval quality, operational resilience, and deployment architecture based on real requirements.
