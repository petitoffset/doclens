# PB-1206: Alert webhooks failed signature verification

**Status:** Resolved  
**Workspace plan:** Business  
**Area:** Webhook delivery

## Reported symptom

Alert emails arrived normally, but the corresponding webhook endpoint rejected every request with `401 Unauthorized`. The alert itself was visibly in the `Firing` state, so the team initially suspected that PulseBoard had signed the wrong event.

## Investigation

The delivery history contained the initial request and three retries after 1, 5, and 15 minutes. Each request received a `401` response within the five-second timeout. The event identifier stayed the same across attempts, confirming that these were delivery retries rather than new alert transitions.

The receiver parsed the JSON payload, serialized it again with different whitespace, and calculated HMAC-SHA256 over the new string. PulseBoard signs the exact raw request bytes. Although the parsed JSON represented the same values, its byte sequence no longer matched `X-PulseBoard-Signature`.

Endpoint TLS, the configured secret, and workspace plan were correct. Redirect handling and rate limiting were unrelated to the failure.

## Resolution

The receiver was changed to preserve the raw request body and verify its HMAC-SHA256 digest before JSON parsing. A test notification then returned `204 No Content`, which PulseBoard recorded as a successful `2xx` delivery.

## Prevention

Webhook handlers should verify the raw bytes with a timing-safe comparison and process the event identifier idempotently. Delivery records remain available for seven days and should be checked independently from alert evaluation history.
