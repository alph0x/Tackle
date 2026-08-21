# Plan — webhook ingestion

**Methodology: Tackle 6.0.0**

## Objective

Accept webhook deliveries from partner services, validate them, persist the events, and retry failed downstream deliveries — observably, with a runnable done-signal per point.

## Non-goals

- No partner-facing dashboard.
- No webhook UI.

## Point decomposition

| P-xx | What | Depends-on | Touches |
|---|---|---|---|
| P-01 | Parse the incoming webhook payload into a normalized event | — | `src/parse.py` |
| P-02 | Validate the HMAC signature of the delivery | P-01 (consumes the parsed payload) | `src/verify.py` |
| P-03 | Persist the normalized event to the events table | P-01 (consumes the parsed payload) | `src/store.py` |
| P-04 | Retry failed downstream deliveries with backoff | P-02 (only verified events), P-03 (only persisted events) | `src/retry.py` |
