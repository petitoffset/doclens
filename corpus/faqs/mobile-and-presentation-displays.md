# Mobile and presentation displays FAQ

PulseBoard dashboards can be viewed in a mobile browser. Business workspaces can also publish a temporary presentation link for a wall display or operations screen.

## What can I do from a mobile browser?

The responsive dashboard view supports filtering, opening widget details, and acknowledging active alerts. Creating or rearranging widgets, editing alert rules, uploading CSV files, and changing workspace settings require the desktop interface.

Mobile dashboards follow the same data rules as desktop dashboards: a visible page refreshes every 30 seconds, and an absolute time range does not move forward automatically. Switching away from the browser for more than five minutes pauses refresh until the page is active again.

## How do presentation links work?

An Admin in a Business workspace can create a view-only link for a dashboard. The link expires after seven days unless it is revoked earlier. It does not allow viewers to acknowledge alerts, inspect workspace members, download exports, or edit the dashboard.

Presentation mode requests dashboard updates every 30 seconds while the display remains awake and connected. It does not change ingestion speed or bypass the 15-second query cache. If the display shows a fixed absolute range, new events outside that range will not appear even though refresh is working.

Starter does not include presentation links. Sharing a screenshot or exported file does not create a live display and does not grant access to the underlying dashboard.
