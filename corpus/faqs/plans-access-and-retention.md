# Plans, access, and retention FAQ

PulseBoard offers Starter and Business workspaces. Plan limits apply per workspace rather than per individual member.

## What are the main plan limits?

Starter supports up to 5 members, retains event data for 30 days, and allows 10 alert rules. Business supports up to 50 members, retains event data for 180 days, and allows 100 alert rules.

Both plans include dashboards, manual CSV exports, in-app alerts, and email notifications. Business additionally supports scheduled exports, webhook notifications, SAML single sign-on, audit history, and presentation links for shared displays.

Increasing the plan does not restore data that has already aged out. After an upgrade, newly retained data follows the longer window.

## What can each role do?

Viewers can open dashboards, acknowledge alerts, and download exports that have been shared with them. Analysts can also build dashboards and alert rules and run manual exports. Admins manage members and workspace integrations, including SSO, webhooks, schedules, and presentation links.

Roles control actions but do not extend the workspace retention window. An Admin cannot query or export event data that has already expired.

## How do exports interact with retention?

An export contains only event data that is still retained when the export job starts. A single export can contain at most 100,000 rows. Its download link remains valid for 24 hours, but expiry of the link does not delete the underlying retained events.

Manual CSV exports are available on both plans. Daily and weekly scheduled exports require Business and must be created by an Admin.

## Does PulseBoard support SSO?

Business supports SAML 2.0. PulseBoard accepts up to five minutes of clock difference when validating an assertion, and an authenticated session lasts eight hours. Starter members sign in without workspace SAML.
