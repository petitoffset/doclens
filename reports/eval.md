# DocLens evaluation

Generated: 2026-09-24T22:43:09.590576+00:00

## Configuration

- Golden questions: 12
- Retrieval depth: 3
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Generation model: `gpt-6-luna`
- Judge model: `gpt-6-sol`

## Summary

| Metric | Result |
| --- | ---: |
| Hit@3 | 100.0% |
| MRR@3 | 77.8% |
| Source Recall@3 | 95.8% |
| Correctness | 75.0% |
| Faithfulness | 91.7% |

## Results

### dashboard-refresh-and-cache

**Question:** How often does a visible dashboard refresh, and how stale can a cached result be?

**Reference answer:** A visible dashboard refreshes every 30 seconds. Equivalent queries may return cached results up to 15 seconds old.

**Expected sources:** `specifications/dashboard-refresh.md`

**Retrieval:** Hit@3 1.000, MRR@3 1.000, Source Recall@3 1.000

**Retrieved:**

1. `specifications/dashboard-refresh.md` (chunk 1, distance 0.2921)
2. `faqs/dashboards-and-alerts.md` (chunk 0, distance 0.3691)
3. `specifications/dashboard-refresh.md` (chunk 0, distance 0.3778)

**Answer:** A visible dashboard requests fresh results every 30 seconds. An identical query may return a cached result for up to 15 seconds; manual refresh does not bypass that cache.

**Correctness:** Pass — States the 30-second refresh interval and up-to-15-second cached result age without contradiction.

**Faithfulness:** Pass — The retrieved context supports both timings and says manual refresh does not bypass the cache.

### ingestion-api-429-recovery

**Question:** What should a client do after receiving a 429 response from the PulseBoard ingestion API?

**Reference answer:** The request was not queued. The client should wait for the Retry-After interval before retrying the same batch, reuse its original Idempotency-Key, and use bounded jitter when multiple workers share the workspace limit.

**Expected sources:** `specifications/ingestion-api.md`

**Retrieval:** Hit@3 1.000, MRR@3 0.500, Source Recall@3 1.000

**Retrieved:**

1. `specifications/webhook-delivery.md` (chunk 1, distance 0.3983)
2. `specifications/ingestion-api.md` (chunk 0, distance 0.4037)
3. `support-tickets/PB-1206-webhook-signature-failure.md` (chunk 2, distance 0.4376)

**Answer:** I don't have enough information in the indexed documents to answer that question.

**Correctness:** Fail — It does not provide the required 429 retry instructions.

**Faithfulness:** Pass — The retrieved context does not state what a client should do after a 429 response.

### csv-atomic-validation

**Question:** What happens when one row in a CSV import is invalid, and how many validation errors are reported?

**Reference answer:** CSV validation is atomic, so one invalid required value causes the whole file to be rejected before any rows are ingested. PulseBoard reports at most 100 validation errors.

**Expected sources:** `specifications/csv-import.md`

**Retrieval:** Hit@3 1.000, MRR@3 1.000, Source Recall@3 1.000

**Retrieved:**

1. `specifications/csv-import.md` (chunk 1, distance 0.3037)
2. `support-tickets/PB-1087-csv-import-failure.md` (chunk 0, distance 0.3536)
3. `faqs/data-ingestion.md` (chunk 2, distance 0.4197)

**Answer:** The entire CSV import is rejected before any rows are ingested; there is no partial import. The validation report includes at most the first 100 errors, with row numbers.

**Correctness:** Pass — It states that the whole import is rejected before ingestion and that at most 100 errors are reported.

**Faithfulness:** Pass — The retrieved context explicitly supports atomic rejection and a report of at most the first 100 errors with row numbers.

### alert-fire-and-recovery

**Question:** How many evaluations make a threshold alert fire and later return it to normal?

**Reference answer:** A threshold alert fires after three consecutive breaching evaluations and returns to Normal after two consecutive healthy evaluations.

**Expected sources:** `specifications/alert-evaluation.md`

**Retrieval:** Hit@3 1.000, MRR@3 1.000, Source Recall@3 1.000

**Retrieved:**

1. `specifications/alert-evaluation.md` (chunk 0, distance 0.2921)
2. `faqs/dashboards-and-alerts.md` (chunk 1, distance 0.3532)
3. `support-tickets/PB-1178-alert-not-triggered.md` (chunk 1, distance 0.4037)

**Answer:** A threshold alert fires after **3 consecutive breached evaluations** and returns to normal after **2 consecutive healthy evaluations**.

**Correctness:** Pass — The answer gives three consecutive breached evaluations to fire and two consecutive healthy evaluations to return to normal.

**Faithfulness:** Pass — Both counts and state transitions are explicitly supported by the retrieved context.

### webhook-retries

**Question:** When a PulseBoard webhook delivery fails, what retry schedule is used and are redirects followed?

**Reference answer:** After the initial failure, PulseBoard retries after 1, 5, and 15 minutes. Redirects are not followed; a 3xx response is recorded as a failed delivery.

**Expected sources:** `specifications/webhook-delivery.md`

**Retrieval:** Hit@3 1.000, MRR@3 1.000, Source Recall@3 1.000

**Retrieved:**

1. `specifications/webhook-delivery.md` (chunk 2, distance 0.1993)
2. `faqs/notification-delivery.md` (chunk 0, distance 0.2856)
3. `faqs/notification-delivery.md` (chunk 1, distance 0.2979)

**Answer:** Failed webhook deliveries are retried after 1, 5, and 15 minutes. Redirect responses count as failed attempts; they are not followed.

**Correctness:** Pass — The answer gives the 1-, 5-, and 15-minute retry schedule and says redirects are not followed and count as failures.

**Faithfulness:** Pass — The context states the retry schedule and treats redirects as failed attempts, supporting the answer.

### plan-capacity-and-retention

**Question:** How do Starter and Business differ in workspace members and event retention?

**Reference answer:** Starter supports 5 workspace members and retains event data for 30 days. Business supports 50 members and retains event data for 180 days.

**Expected sources:** `specifications/access-exports-and-retention.md`

**Retrieval:** Hit@3 1.000, MRR@3 0.333, Source Recall@3 1.000

**Retrieved:**

1. `faqs/plans-access-and-retention.md` (chunk 0, distance 0.3683)
2. `specifications/audit-log.md` (chunk 0, distance 0.4381)
3. `specifications/access-exports-and-retention.md` (chunk 0, distance 0.4842)

**Answer:** Starter supports up to 5 workspace members and retains event data for 30 days. Business supports up to 50 members and retains event data for 180 days.

**Correctness:** Pass — Both plan member limits and event-retention periods match the reference.

**Faithfulness:** Pass — The retrieved plan documents support all four limits stated.

### audit-log-coverage

**Question:** Does the audit log record dashboard views or query text, and how long is it retained?

**Reference answer:** The audit log does not record ordinary dashboard views or dashboard query text. Audit records are retained for 90 days.

**Expected sources:** `specifications/audit-log.md`

**Retrieval:** Hit@3 1.000, MRR@3 1.000, Source Recall@3 1.000

**Retrieved:**

1. `specifications/audit-log.md` (chunk 0, distance 0.3508)
2. `specifications/audit-log.md` (chunk 1, distance 0.4858)
3. `specifications/access-exports-and-retention.md` (chunk 0, distance 0.5475)

**Answer:** The audit log does **not** record ordinary dashboard views or dashboard query text (or results). It is retained for **90 days**.

**Correctness:** Pass — States that ordinary dashboard views and query text are not recorded and retention is 90 days.

**Faithfulness:** Pass — The context explicitly supports the exclusions, including results, and the 90-day retention period.

### csv-support-incident

**Question:** Why was the CSV in support ticket PB-1087 rejected, and what fixed it?

**Reference answer:** The CSV was encoded as UTF-16 LE and used local timestamps without a UTC designator or numeric offset, so atomic validation rejected the whole file. Exporting it as UTF-8 with ISO 8601 UTC timestamps and uploading the corrected file fixed the import.

**Expected sources:** `support-tickets/PB-1087-csv-import-failure.md`

**Retrieval:** Hit@3 1.000, MRR@3 1.000, Source Recall@3 1.000

**Retrieved:**

1. `support-tickets/PB-1087-csv-import-failure.md` (chunk 0, distance 0.4084)
2. `faqs/data-ingestion.md` (chunk 2, distance 0.5199)
3. `specifications/csv-import.md` (chunk 0, distance 0.5585)

**Answer:** The CSV was rejected because it was encoded as UTF-16 LE and used ambiguous local timestamps such as `03/08/2026 09:15`. PulseBoard requires UTF-8 and ISO 8601 timestamps with `Z` or an explicit numeric offset. Validation is atomic, so no rows were imported. The file’s size, row count, headers, and numeric values were not the cause.

To fix it, re-export or convert the CSV to UTF-8 and format `event_time` values as unambiguous ISO 8601 timestamps with a timezone designator or offset.

**Correctness:** Fail — It explains the rejection and required corrections but omits that uploading the corrected file fixed the import.

**Faithfulness:** Pass — All factual claims are supported by the retrieved context.

### accepted-events-to-dashboard

**Question:** After an API batch receives 202 Accepted, when should its events appear on a visible dashboard?

**Reference answer:** A 202 response means the batch is durably queued, not yet queryable. Under normal load it becomes queryable within 60 seconds; after that, a visible dashboard queries every 30 seconds and equivalent results may remain cached for up to 15 seconds.

**Expected sources:** `specifications/ingestion-api.md`, `specifications/dashboard-refresh.md`

**Retrieval:** Hit@3 1.000, MRR@3 0.500, Source Recall@3 1.000

**Retrieved:**

1. `support-tickets/PB-1134-delayed-dashboard-data.md` (chunk 0, distance 0.3348)
2. `specifications/dashboard-refresh.md` (chunk 0, distance 0.3747)
3. `specifications/ingestion-api.md` (chunk 1, distance 0.4045)

**Answer:** A `202 Accepted` confirms the events were queued, not immediately visible. Under normal conditions, they become queryable within 60 seconds and should appear on the next dashboard query—typically within another 30 seconds, or immediately after a manual refresh. The dashboard’s time range must include the events. Historical backfills or degraded processing may take up to ten minutes.

**Correctness:** Fail — It omits the possible 15-second cache delay and implies the next query or manual refresh will show the events.

**Faithfulness:** Fail — The context supports immediate query submission on manual refresh, not guaranteed immediate visibility; it notes that caches can apply after processing.

### alert-webhook-failure

**Question:** If an alert fires but its webhook receiver returns an error, does PulseBoard rerun the alert evaluation and how is delivery retried?

**Reference answer:** No. A delivery failure does not rerun the alert query or create a new alert transition. Webhook delivery is retried separately after 1, 5, and 15 minutes.

**Expected sources:** `specifications/alert-evaluation.md`, `specifications/webhook-delivery.md`

**Retrieval:** Hit@3 1.000, MRR@3 0.500, Source Recall@3 0.500

**Retrieved:**

1. `faqs/notification-delivery.md` (chunk 0, distance 0.1986)
2. `specifications/webhook-delivery.md` (chunk 2, distance 0.2097)
3. `support-tickets/PB-1178-alert-not-triggered.md` (chunk 1, distance 0.2671)

**Answer:** No. A webhook error does not rerun the alert evaluation or create a new alert transition. PulseBoard retries delivery after 1, 5, and 15 minutes. The retries use the same notification event ID, with a new attempt number, and do not reset the rule’s cooldown.

**Correctness:** Pass — It states that webhook failure does not rerun evaluation or create a new transition, and gives the 1-, 5-, and 15-minute retry schedule.

**Faithfulness:** Pass — The retrieved context supports every claim, including the shared event ID, new attempt number, and unchanged cooldown.

### presentation-link-access

**Question:** Who can create a presentation link, on which plan, and how does the shared dashboard behave?

**Reference answer:** A Business workspace Admin can create a presentation link. It is view-only, expires after seven days unless revoked earlier, and refreshes the dashboard every 30 seconds.

**Expected sources:** `faqs/mobile-and-presentation-displays.md`

**Retrieval:** Hit@3 1.000, MRR@3 0.500, Source Recall@3 1.000

**Retrieved:**

1. `specifications/dashboard-refresh.md` (chunk 2, distance 0.4182)
2. `faqs/mobile-and-presentation-displays.md` (chunk 0, distance 0.4969)
3. `faqs/mobile-and-presentation-displays.md` (chunk 1, distance 0.5371)

**Answer:** An Admin in a Business workspace can create a presentation link. It provides view-only access to a single dashboard and expires after seven days unless revoked. The display requests updates every 30 seconds while awake and connected, subject to the 15-second query cache; a fixed absolute time range won’t advance to include newer events. Starter doesn’t include presentation links.

**Correctness:** Pass — Includes the required creator, plan, view-only access, seven-day expiration, and 30-second refresh.

**Faithfulness:** Pass — All factual claims are supported by the retrieved context.

### scheduled-export-audit

**Question:** Can a Starter workspace schedule exports, and is export creation recorded in the audit log?

**Reference answer:** No. Starter workspaces cannot schedule exports. Export creation is recorded in the audit log.

**Expected sources:** `specifications/access-exports-and-retention.md`, `specifications/audit-log.md`

**Retrieval:** Hit@3 1.000, MRR@3 1.000, Source Recall@3 1.000

**Retrieved:**

1. `specifications/audit-log.md` (chunk 1, distance 0.3571)
2. `specifications/audit-log.md` (chunk 0, distance 0.3672)
3. `specifications/access-exports-and-retention.md` (chunk 1, distance 0.4552)

**Answer:** No. Starter does not support scheduled exports. Export creation (manual or scheduled) is recorded in the Business audit log, which is available only on Business.

**Correctness:** Pass — It states that Starter cannot schedule exports and that export creation is recorded in the audit log.

**Faithfulness:** Pass — The context supports Starter’s lack of schedules, the logging of manual and scheduled export creation, and audit-log availability only on Business.
