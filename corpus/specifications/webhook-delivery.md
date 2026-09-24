# Webhook delivery specification

This specification defines outbound PulseBoard webhook delivery. Webhooks are a Business notification channel and are distinct from the event ingestion API.

## Endpoint configuration

An Admin may configure up to five webhook endpoints in a Business workspace. Endpoints must use HTTPS. PulseBoard does not follow HTTP redirects, so a `3xx` response is recorded as a failed delivery.

Starter workspaces cannot configure webhook endpoints. This restriction does not affect email or in-app alert notifications.

## Request signing

PulseBoard signs every request with HMAC-SHA256 and places the digest in `X-PulseBoard-Signature`. The signature input is the exact raw request body bytes. Receivers must verify those bytes before parsing or transforming the JSON.

Reformatting JSON, changing whitespace, changing character escaping, or using an obsolete endpoint secret produces a different digest. Signature comparison should be performed with a timing-safe function.

## Success, timeout, and retries

Any HTTP `2xx` response received within five seconds marks the delivery successful. PulseBoard treats timeouts, network failures, redirects, and all non-`2xx` statuses as failed attempts.

After the initial failure, PulseBoard retries after 1 minute, 5 minutes, and 15 minutes. The retry sequence concerns delivery only: it does not re-run the alert query, create a new alert transition, or reset the alert rule's cooldown.

Each attempt carries the same notification event identifier but a new delivery-attempt number. Operators should make receivers idempotent so a late response followed by a retry does not duplicate downstream work.

## Delivery history

PulseBoard retains webhook delivery records for seven days. Records include the endpoint, attempt time, response status or timeout, and event identifier. They do not store the receiver's response body. Delivery history can confirm that a rule fired even if the receiver rejected every attempt.
