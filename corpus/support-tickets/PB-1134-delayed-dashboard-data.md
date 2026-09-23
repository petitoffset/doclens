# PB-1134: Accepted events did not appear on an operations dashboard

**Status:** Resolved  
**Workspace plan:** Business  
**Area:** Dashboard freshness

## Reported symptom

An API batch sent at 14:02 UTC received `202 Accepted`, but an operations dashboard still showed no new points several minutes later. Manual refresh did not change the chart, and the team suspected a processing outage.

## Investigation

Ingestion diagnostics showed that the batch became queryable 47 seconds after acceptance, within the normal 60-second processing target. No rate limit or validation errors occurred.

The affected dashboard used an absolute time range ending at 14:00 UTC. Refreshing repeated the query with that fixed end time, so events timestamped after 14:00 remained outside the chart. The tab had also spent more than five minutes in the background, which paused its automatic 30-second refresh, but this was not the primary reason the events stayed absent after a manual refresh.

The same events appeared in a search covering the correct interval, confirming that ingestion and retention were operating normally.

## Resolution

The operator changed the dashboard to a relative “last 15 minutes” range and requested a manual refresh. The new query included the 14:02 events, and the chart populated immediately.

## Prevention

Operational dashboards that should advance with current time should use relative ranges. An HTTP `202` confirms queueing rather than instant visibility, but once data is queryable, repeated refreshes cannot bring it into a fixed interval that excludes its timestamp.
