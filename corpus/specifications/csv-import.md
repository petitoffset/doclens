# CSV import specification

This specification defines validation and processing for CSV files uploaded to PulseBoard.

## File limits

A CSV file may be no larger than 20 MiB and may contain at most 50,000 data rows. The header row does not count toward the row limit. Files must be encoded as UTF-8; UTF-16 and locale-specific legacy encodings are not accepted.

Every file must contain these columns:

- `event_time`
- `metric`
- `value`

Additional columns are stored as string attributes. Column names are case-sensitive and leading or trailing whitespace is significant.

## Values and timestamps

`event_time` must be an ISO 8601 timestamp with either the `Z` UTC designator or an explicit numeric offset, such as `2026-03-08T09:15:00Z` or `2026-03-08T10:15:00+01:00`. Ambiguous local dates such as `03/08/2026 09:15` are rejected.

`metric` must be a non-empty string. `value` must parse as a finite number; empty values, infinities, and text placeholders are invalid.

## Atomic validation

PulseBoard validates the complete file before queueing any rows. If one or more rows are invalid, the import is rejected and zero events are ingested. The validation report includes at most the first 100 errors with row numbers. Corrected files must be uploaded as new imports.

This atomic behavior prevents a user from mistaking a partially imported file for a complete data set.

## Processing

After validation succeeds, PulseBoard queues the file for ingestion. A valid import normally completes within ten minutes. The import status distinguishes `Validating`, `Processing`, `Complete`, and `Rejected`.

CSV processing time does not alter dashboard refresh behavior. A dashboard can show imported events only after the import reaches `Complete`, the events fall inside the selected time range, and the dashboard issues a new query.

CSV uploads are ingestion inputs, not retained source files. PulseBoard persists the processed event records and import metadata but does not provide the original uploaded file for later download.
