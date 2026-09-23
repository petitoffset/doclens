# Access, exports, and retention specification

This specification defines PulseBoard workspace plans, roles, event retention, and export behavior.

## Plans and retention

Starter workspaces support 5 members and retain event data for 30 days. Business workspaces support 50 members and retain event data for 180 days. Retention is evaluated continuously at the workspace level.

Expired events are deleted from the queryable data set. Upgrading a workspace changes retention for data that remains present; it does not recover events that were already deleted.

## Roles

PulseBoard has three workspace roles:

- **Viewer:** view dashboards, acknowledge alerts, and download exports shared with them.
- **Analyst:** all Viewer actions plus dashboard and alert editing and manual exports.
- **Admin:** all Analyst actions plus member administration, SSO configuration, webhook management, scheduled exports, and presentation-link creation.

Roles grant actions but cannot override plan availability or retention.

## Exports

Manual CSV exports are available on both plans and may be started by Analysts or Admins. An export may contain at most 100,000 rows. If a query produces more rows, the export fails rather than silently truncating the result.

Business Admins may create daily or weekly export schedules. Scheduled export jobs use the same row limit and retention boundary as manual jobs. Starter does not support schedules.

An export evaluates retention when its job starts. Events that have already expired cannot be included. A completed export's download link is valid for 24 hours. Link expiry does not change source-event retention and does not extend access to the workspace.

## SAML single sign-on

Business supports SAML 2.0 configuration by an Admin. PulseBoard accepts an assertion clock difference of up to five minutes and creates an eight-hour session after successful authentication. Starter does not support workspace SAML.

Authentication does not change the user's assigned PulseBoard role. A successfully authenticated Viewer remains unable to create exports or edit dashboards.
