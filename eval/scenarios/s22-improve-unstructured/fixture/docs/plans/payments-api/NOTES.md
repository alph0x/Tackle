# payments-api — raw notes

Freeform thoughts, no particular order:

- migrate payments to the new gateway
- retry logic: exponential backoff? max 3 tries?
- webhooks currently unreliable, drop events?
- invoice emails should be HTML
- who owns the legacy service?
- migration window: maybe a weekend
- rate limiting on /v1/charges?
- stripe vs adyen — still open
- team said something about idempotency keys
- cutover: feature flag?
