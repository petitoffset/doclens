# PB-1087: CSV import was rejected before processing

**Status:** Resolved  
**Workspace plan:** Starter  
**Area:** CSV import

## Reported symptom

A user uploaded a 12 MiB CSV containing 18,204 data rows. The import moved from `Validating` to `Rejected` and no measurements appeared on the dashboard. Because the file was below both the size and row limits, the user expected partial ingestion.

## Investigation

The file had been exported from a desktop spreadsheet as UTF-16 LE. Its `event_time` values used forms such as `03/08/2026 09:15`, with no UTC designator or numeric offset.

PulseBoard requires UTF-8 input and unambiguous ISO 8601 timestamps. The validation report showed the first 100 timestamp errors. CSV validation is atomic, so the failure occurred before any rows were queued; there was no partial data set to remove.

The required `event_time`, `metric`, and `value` headers were present, and the numeric values were valid. File size and row count were not the cause.

## Resolution

The source system exported the file as UTF-8 and converted timestamps to values such as `2026-03-08T09:15:00Z`. The corrected file passed validation, entered `Processing`, and reached `Complete` after seven minutes.

The dashboard showed the imported events on its next refresh because they fell inside the selected relative time range.

## Prevention

The team added an export check for UTF-8 and ISO 8601 timestamps before future uploads. Rejected files should be corrected and uploaded again; PulseBoard does not retain an original upload for later repair.
