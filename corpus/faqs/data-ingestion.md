# Data ingestion FAQ

PulseBoard accepts operational event data through the batch API or a CSV upload. Both methods feed the same processing pipeline and make data available to dashboards, searches, and alert evaluation after processing completes.

## Which ingestion method should I use?

Use the API for continuous delivery from an application or integration. A single API request can contain up to 500 events and an uncompressed JSON body no larger than 2 MiB. The limit applies to the entire workspace, so several API clients sending at once share the same request allowance.

Use CSV for a one-time import or a moderate historical backfill. A CSV can contain at most 50,000 data rows and must be 20 MiB or smaller. Larger backfills should be divided into multiple files and uploaded sequentially.

## When will accepted data appear?

An HTTP `202` response means that an API batch has entered the processing queue; it does not mean the events are already queryable. Under normal load, API events become available within about one minute. A large backfill or a busy processing period can take up to ten minutes.

CSV imports are validated before they enter the queue and normally finish within ten minutes. The import status page shows whether validation or processing is still underway.

## Why was my API client rate limited?

Each workspace can submit 300 API requests per minute. When the shared limit is exceeded, PulseBoard returns `429 Too Many Requests` with a `Retry-After` header. Wait for that interval before retrying. Immediate, repeated retries extend the backlog and do not bypass the limit.

Clients that retry should provide an `Idempotency-Key`. PulseBoard remembers a key for 24 hours, which prevents the same batch from being inserted twice after a timeout or uncertain response.

## Why was a CSV rejected before importing any rows?

CSV validation is atomic. If a required value is invalid, PulseBoard rejects the file before ingesting any rows and reports up to 100 validation errors. Files must be UTF-8 and include `event_time`, `metric`, and `value`. Event timestamps must use ISO 8601 with either `Z` or an explicit numeric offset.
