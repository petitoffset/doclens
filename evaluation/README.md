# DocLens evaluation

DocLens evaluates retrieval and grounded answer quality against a small, manually reviewed golden dataset. The subsystem is intentionally inspectable: every aggregate score can be traced to a question, expected source set, retrieved chunks, generated answer, and judge rationale.

## Artifacts

| Artifact | Purpose |
| --- | --- |
| [`golden.json`](golden.json) | 12 product questions, reference answers, and expected source documents |
| [`backend/app/evaluation.py`](../backend/app/evaluation.py) | Dataset validation, metrics, judging, and report rendering |
| [`backend/scripts/run_evaluation.py`](../backend/scripts/run_evaluation.py) | Evaluation runner using the production ingestion and retrieval path |
| [`reports/eval.md`](../reports/eval.md) | Generated baseline with configuration and per-case evidence |

The dataset covers both single-source and multi-source questions. It measures product-answer quality only; deterministic security tests and the manual prompt-injection demonstration remain separate.

## Evaluation flow

```text
golden case
  -> production corpus ingestion and top-3 retrieval
  -> retrieval metrics against expected source documents
  -> grounded answer generation from retrieved chunks
  -> separate LLM judge
       correctness: answer vs reference answer
       faithfulness: answer vs retrieved context
  -> reports/eval.md
```

## Metrics

### Retrieval

- **Hit@3:** 1 when at least one expected source document appears in the top three, otherwise 0.
- **MRR@3:** reciprocal rank of the first expected source in the top three.
- **Source Recall@3:** fraction of expected source documents represented in the top three. This distinguishes partial retrieval on multi-source questions.

The report presents macro averages across the golden cases.

### Generation

- **Correctness:** whether the generated answer contains the facts required by the reference answer without contradiction.
- **Faithfulness:** whether every factual claim in the generated answer is supported by the retrieved context.

A separate OpenAI call returns binary judgments with short rationales. The generated answer, context-derived source list, and rationale remain visible for manual review.

## Running the evaluation

Create the repository-root configuration if needed:

```powershell
Copy-Item .env.example .env
```

For a full run, set `OPENAI_API_KEY`, `OPENAI_MODEL`, and `OPENAI_JUDGE_MODEL`. The repository-root `.env` is loaded automatically, while existing process environment variables take precedence.

From `backend/`:

```powershell
uv run python -m scripts.run_evaluation
```

The command makes external generation and judge calls, can incur API usage, and overwrites [`reports/eval.md`](../reports/eval.md).

To measure retrieval without external calls:

```powershell
uv run python -m scripts.run_evaluation --retrieval-only
```

## Current baseline

The committed report was generated with:

- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Retrieval depth: 3
- Generation: `gpt-6-luna`
- Judge: `gpt-6-sol`

| Metric | Result |
| --- | ---: |
| Hit@3 | 100.0% |
| MRR@3 | 77.8% |
| Source Recall@3 | 95.8% |
| Correctness | 75.0% |
| Faithfulness | 91.7% |

The [generated report](../reports/eval.md) is the source of truth for per-case results.

## Measurement limitations and findings

- Retrieval metrics operate at document level. The 429 case receives a Hit@3 because the expected document appears, but the answer-bearing chunk is outside the supplied top-three context and generation abstains.
- Top-three retrieval does not enforce source diversity. One multi-source case represents only one of its two expected documents.
- Retrieved evidence does not guarantee a complete answer. In the accepted-events case, generation omits the possible cache delay and overstates immediate visibility after manual refresh.
- The CSV support-ticket result is borderline and judge-sensitive: the generated answer gives the corrective steps but does not explicitly state that uploading the corrected file succeeded.
- Binary LLM judgments are model- and run-dependent. Aggregate scores should be read alongside answers and rationales.
- Twelve synthetic cases are appropriate for an inspectable MVP baseline, not statistical evidence of production quality.

No retrieval or generation settings were tuned after observing this baseline. Known failures are retained as evidence and potential next-step inputs.

## Security validation

Security behavior is not included in the golden quality dataset:

- deterministic upload, filename, size, query-length, and prompt-boundary checks live under [`backend/tests/`](../backend/tests/);
- two live-model prompt-injection scenarios are defined in [`backend/scripts/demo_prompt_injection.py`](../backend/scripts/demo_prompt_injection.py).

This separation keeps repeatable input controls distinct from qualitative model-behavior demonstrations.
