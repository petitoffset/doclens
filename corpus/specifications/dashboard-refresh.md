# Dashboard query and refresh specification

This specification defines how PulseBoard dashboards query processed event data.

## Queryable data

Dashboards query only events that have completed ingestion. A `202 Accepted` API response or a CSV in `Processing` state does not make data immediately visible. Under normal conditions, API data becomes queryable within 60 seconds; completed CSV imports have already passed through processing.

Event retention is applied before query execution. Changing roles, refreshing the browser, or upgrading a plan cannot restore events that have already expired.

## Refresh behavior

A visible dashboard automatically submits a query every 30 seconds. A manual refresh submits a query immediately. Automatic refresh pauses after the browser tab has remained in the background for five minutes and resumes when the tab becomes active.

Equivalent workspace queries may return cached results for up to 15 seconds. A manual refresh does not bypass this cache. The cache duration is measured independently from the dashboard's 30-second schedule.

## Time ranges

A relative time range, such as the last 15 minutes, recalculates its start and end on every query. An absolute time range keeps its configured boundaries. Data outside an absolute range will not appear merely because the dashboard refreshes.

All event timestamps are normalized for query evaluation. Display timezone changes labels and grouping presentation but does not move an event into or out of an absolute UTC interval.

## Dashboard limits

A dashboard may contain up to 20 widgets. Each widget issues its own query, although identical queries can share cached results. Reaching the widget limit does not change the workspace ingestion rate or the number of alert rules allowed by its plan.

Dashboard edit permission is separate from viewing permission. Viewers may open dashboards, while Analysts and Admins may create and edit them. Presentation links are a Business feature and provide view-only access to a single dashboard.
