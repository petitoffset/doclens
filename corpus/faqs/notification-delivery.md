# Notification delivery FAQ

Alert evaluation decides when a PulseBoard rule changes state. Notification delivery begins only after that state change, so delivery time and rule evaluation time should be diagnosed separately.

## How quickly are notifications delivered?

In-app notifications are created when the rule enters the firing state. Email is queued at the same time and normally arrives within 60 seconds. If an email provider temporarily rejects the message, PulseBoard makes three delivery attempts within a ten-minute window.

Email retries do not create additional alert transitions and do not reset the rule's 15-minute repeat-notification cooldown. A delayed email can therefore refer to an earlier alert state.

## How are webhooks delivered?

Webhook notifications are available only on Business. PulseBoard treats any HTTP `2xx` response as success. A timeout, redirect, or other status is a failed attempt. Failed deliveries are retried after 1, 5, and 15 minutes.

Each webhook request is signed. Receivers must calculate the HMAC-SHA256 signature from the raw request body rather than from parsed and re-serialized JSON. Delivery history is available for seven days to help distinguish an alert that never fired from a notification that failed downstream.

## Why did email arrive but the webhook did not?

Channels are delivered independently. A valid email address does not confirm that the webhook URL, TLS configuration, response status, or signature verification is correct. Check the alert state first, then inspect the delivery record for the affected channel.
