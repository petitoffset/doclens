# Dashboards and alerts FAQ

Dashboards visualize processed PulseBoard events. Alerts evaluate the same queryable data on a fixed schedule, but dashboard refreshes and alert state changes are separate processes.

## How often does a dashboard update?

An open, visible dashboard requests fresh results every 30 seconds. Repeated identical queries may use cached results for up to 15 seconds. You can request a manual refresh, but it cannot display events that are still in the ingestion queue.

To limit browser and network usage, automatic refresh pauses after a tab has remained in the background for five minutes. Returning to the tab resumes refresh. A relative range such as “last 15 minutes” advances on each refresh; an absolute start and end time remains fixed until edited.

## When does a threshold alert fire?

PulseBoard evaluates alert rules once per minute. A threshold must be breached in three consecutive evaluations before the rule enters the firing state. A short spike that is healthy by the third evaluation does not trigger a notification.

A firing rule returns to normal after two consecutive healthy evaluations. While it remains firing, repeat notifications are limited by a 15-minute cooldown. Missing data for two consecutive evaluations changes the rule to `Unknown` rather than treating the missing values as either healthy or breached.

## What happens during maintenance?

Rule evaluation continues, but PulseBoard suppresses notifications during a configured maintenance window. If the rule is still firing when maintenance ends, it sends a notification after the next evaluation. Maintenance does not rewrite earlier measurements or change dashboard visibility.

## Which notification channels are available?

In-app and email notifications are available on both plans. Business workspaces can also send alert events to HTTPS webhooks. Delivery retries are handled by the notification channel and do not cause the alert rule to be evaluated again.
