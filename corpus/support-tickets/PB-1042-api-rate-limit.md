# PB-1042: Backfill repeatedly hit the API rate limit

**Status:** Resolved  
**Workspace plan:** Business  
**Area:** Event ingestion API

## Reported symptom

A workspace started a six-month backfill with 20 parallel workers. The first requests received `202 Accepted`, but most later requests returned `429 Too Many Requests`. The workers retried immediately, and dashboard data appeared several minutes behind the source system.

The operator was concerned that the rate-limit responses meant accepted events had been lost.

## Investigation

The workers were sending roughly 900 batch requests per minute to one workspace. PulseBoard allows 300 requests per minute per workspace, shared across all API keys. Every worker had been configured as if it owned the full workspace allowance.

The retry code ignored `Retry-After` and generated more rejected traffic. It also created a new idempotency key on every retry, which would not have protected against duplicates if a response had been lost after queueing.

Ingestion records confirmed that batches returning `202` were queued. Requests returning `429` were not queued. Once traffic was reduced, the accepted backlog became queryable within eight minutes, which was inside the documented ten-minute backfill window.

## Resolution

The workspace applied a shared limiter capped below 300 requests per minute. Workers now wait for the `Retry-After` duration with small random jitter and reuse the original `Idempotency-Key` when retrying the same batch.

The backfill completed without duplicate or missing accepted batches. Dashboard freshness returned to the normal processing range after the backlog cleared.

## Prevention

Backfill clients must coordinate traffic at workspace level. Increasing worker count does not increase the workspace request allowance, and immediate retries make recovery slower.
