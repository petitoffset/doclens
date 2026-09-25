# DocLens Implementation Plan

This roadmap tracks the five milestones required to deliver the focused DocLens MVP. Each milestone keeps its current status alongside its scope so progress is clear without a separate tracker.

## 1. Project foundation

**Status:** Completed

Establish the repository baseline needed for implementation:

- Repository metadata and project instructions
- Project planning documentation
- Synthetic corpus
- Initial repository structure

## 2. Ingestion and persistent retrieval

**Status:** Completed

Build one retrieval path for both bundled and user-provided documents:

- Shared ingestion pipeline for the bundled corpus and uploaded `.md`/`.txt` files
- File validation and safe filename sanitization
- Text chunking
- Local embeddings with Sentence Transformers
- Persistent local ChromaDB storage
- Semantic top-3 retrieval
- Retrieval tests and deterministic ingestion guardrail tests

## 3. Grounded answering and observability

**Status:** Completed

Add traceable answer generation and essential runtime safeguards:

- Query endpoint with query-length validation
- OpenAI-based generation using only retrieved context
- Prompt-level abstention when context is insufficient
- Source attribution from retrieved metadata
- Structured JSON logging
- One or two prompt-injection demo scenarios
- API tests with mocked external calls where appropriate

## 4. Minimal frontend

**Status:** Completed

Provide a React single-page interface for the complete user flow:

- Document upload
- Bundled corpus indexing
- Question submission
- Answer and source rendering
- Loading and error states

## 5. Evaluation and documentation

**Status:** Completed

Measure RAG quality and document the finished MVP:

- Small, manually verifiable golden dataset for retrieval and answer quality
- Retrieval metrics:
  - Hit@3
  - MRR@3
  - Source Recall@3: for multi-source questions, the fraction of expected source documents represented in the top three results
- Generation metrics: correctness and faithfulness using a separate LLM judge
- Automatic generation of `reports/eval.md`
- Sanitized example runtime logs
- Final README and `DECISIONS.md` updates
- Limitations and production next steps

## Out of scope for MVP

- LangChain
- Reranking
- Authentication
- Chat history
- Multiple LLM providers
- Background jobs
- Deployment infrastructure
- Comprehensive automated prompt-injection benchmarking
