# PB-1178: CPU threshold alert did not trigger during a short spike

**Status:** Resolved  
**Workspace plan:** Business  
**Area:** Alert evaluation

## Reported symptom

An Analyst expected an alert configured for CPU above 80 percent to fire during a brief spike. The dashboard displayed values above the threshold, but there was no in-app notification, email, or webhook delivery record.

## Investigation

The alert was enabled and its channels were configured correctly. There was no maintenance window, and the relevant events had completed ingestion before each evaluation.

The evaluation history showed:

- 09:11 UTC: 84 percent, first breach
- 09:12 UTC: 86 percent, second consecutive breach
- 09:13 UTC: 79 percent, healthy

PulseBoard evaluates once per minute and requires three consecutive breached evaluations before entering `Firing`. The healthy third evaluation reset the breach counter, so no alert transition occurred. Because the rule never fired, there were correctly no channel delivery attempts to retry.

## Resolution

Support explained the consecutive-evaluation requirement and confirmed that the system behaved as configured. The team kept the rule unchanged because it was intended to ignore spikes shorter than approximately three evaluation intervals.

## Prevention

When investigating a missing notification, first check the alert state and evaluation history. Notification delivery records are relevant only after a rule enters `Firing`; email or webhook retry behavior cannot compensate for a threshold that never met its firing condition.
