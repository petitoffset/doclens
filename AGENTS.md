# Project Instructions

## Project principles

- DocLens is an evolving personal RAG application, not a production-ready system.
- Prefer simple, explicit implementations and incremental, testable improvements.
- Do not expand scope without explicit approval.
- Introduce new frameworks, retrieval techniques, or infrastructure only when their value is justified and the change is explicitly approved.
- Never invent evaluation results.
- Never commit secrets or API keys.
- Keep documentation concise.

## Technical direction

- Use Python and FastAPI for the backend.
- Use React for the frontend.
- Use Sentence Transformers for local embeddings.
- Use a local persistent ChromaDB vector store.
- Use the external OpenAI API only for grounded answer generation and LLM-based evaluation.
- Send only retrieved context to the external LLM.

## Git workflow

- Never work directly on `main`.
- Use a dedicated branch for each milestone or coherent change.
- Never commit without explicit user approval.
- Before requesting commit approval, summarize the changes and validation performed.
- Never push or open a pull request without explicit user approval.
- Never merge pull requests.
