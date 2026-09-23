# Event ingestion API specification

This specification defines the current behavior of the PulseBoard event ingestion API.

## Endpoint and request format

Clients submit events to `POST /v1/events/batch` as a JSON array. A request may contain no more than 500 events, and the uncompressed request body may not exceed 2 MiB. Compression does not increase the permitted uncompressed size.

Each event must include an event timestamp, a metric name, and a numeric value. Additional string attributes may be supplied for filtering and grouping. Validation failure returns a `4xx` response and the rejected request is not queued.

## Acceptance and processing

A valid batch receives `202 Accepted` after it has been placed on the workspace processing queue. Acceptance confirms durable queueing, not immediate search or dashboard availability.

Under normal load, accepted API events are queryable within 60 seconds. Historical backfills or degraded processing may take as long as ten minutes. Dashboard refresh intervals and caches apply only after processing makes the events queryable.

## Rate limiting

Each workspace may send 300 batch requests per minute. All API keys and clients in that workspace share the allowance. The event count does not change the request calculation: a batch of one event and a batch of 500 events each consume one request.

When the limit is exhausted, PulseBoard returns `429 Too Many Requests` and a `Retry-After` header containing a delay in seconds. The rejected request is not queued. Clients must wait for the stated interval before retrying; bounded jitter is recommended when several workers share a workspace.

## Idempotent retries

Clients may send an `Idempotency-Key` header. PulseBoard retains the key and the outcome for 24 hours. Repeating the same request with the same key returns the original acknowledgement without inserting duplicate events.

Reusing a retained key with a different request body returns `409 Conflict`. After 24 hours, the key is no longer recognized, so clients must not rely on it to deduplicate older retries.

## Client recovery guidance

Retry `429` responses only after `Retry-After`. A transient `5xx` or network timeout may be retried with backoff and the original idempotency key. Do not retry validation failures until the request has been corrected. Clients performing backfills should keep their aggregate workspace traffic below the shared request limit rather than assigning the full allowance to every worker.
