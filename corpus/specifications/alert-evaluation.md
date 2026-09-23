# Alert evaluation specification

This specification defines current PulseBoard alert state transitions. Notification delivery is described separately because a rule can fire even when a downstream channel fails.

## Evaluation schedule

PulseBoard evaluates each enabled alert rule once every 60 seconds against queryable event data. Data still waiting in an ingestion queue is not visible to the evaluation.

A threshold rule enters `Firing` only after three consecutive evaluations breach its condition. The breach counter resets when an evaluation is healthy. A firing rule returns to `Normal` after two consecutive healthy evaluations.

If a rule has no usable value for two consecutive evaluations, it enters `Unknown`. Missing data is not treated as zero and does not satisfy either the breach or recovery requirement.

## Notifications and cooldown

Entering `Firing` creates an in-app notification and queues each configured delivery channel. If the rule remains firing, PulseBoard will not send a repeat notification for 15 minutes. The cooldown limits notification frequency; it does not pause evaluation or force the rule back to normal.

In-app and email notifications are supported on Starter and Business. Webhook notification channels require Business. Starter permits up to 10 alert rules per workspace, while Business permits up to 100.

## Maintenance windows

During a configured maintenance window, PulseBoard continues evaluating rules and recording their state but suppresses notifications. If a rule is still firing when the window ends, it sends a notification after the next scheduled evaluation. A rule that recovered before maintenance ended does not produce a delayed firing notification.

Maintenance affects alert delivery only. It does not stop ingestion, change dashboard queries, or extend event retention.

## Permissions

Viewers may see and acknowledge active alerts. Analysts and Admins may create, edit, enable, and disable alert rules. Managing workspace webhook endpoints remains an Admin action even when an Analyst can attach an existing endpoint to a rule.
