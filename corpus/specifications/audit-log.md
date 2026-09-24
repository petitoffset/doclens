# Audit log specification

This specification defines the Business workspace audit log. The audit log records administrative and configuration activity; it is not an event-data archive or a substitute for dashboard history.

## Availability and retention

Audit history is available only on Business and is retained for 90 days. This period is independent of the Business event-data retention period of 180 days. Downgrading to Starter removes access to the audit-log feature but does not extend either retention period.

Audit timestamps are recorded in UTC. Changing a user's display timezone changes presentation only.

## Recorded activity

The audit log records:

- workspace member invitations, removals, and role changes;
- alert rule creation, edits, enabling, and disabling;
- dashboard creation, configuration changes, and deletion;
- manual and scheduled export creation;
- SSO, webhook endpoint, and presentation-link configuration changes.

It does not record ordinary dashboard views, dashboard query text or results, every alert evaluation, or the contents of ingested events. Webhook delivery attempts remain in the separate seven-day delivery history.

## Access and export

Admins may view and export audit history. Analysts and Viewers cannot access it. An audit export may contain at most 50,000 records and is separate from the 100,000-row limit for event-data exports.

Audit exports follow the same 24-hour download-link expiry used by other completed exports. Creating an audit export is itself recorded as an audit event.

## Intended use

Audit records can establish who changed configuration and when. They cannot prove that a dashboard was viewed, explain why an event was absent before ingestion completed, or recover expired event data.
