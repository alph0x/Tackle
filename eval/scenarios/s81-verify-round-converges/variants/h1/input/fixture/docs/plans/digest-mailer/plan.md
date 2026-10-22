# Plan — Digest mailer

## 1. Objective

Subscriber digests go out as queued jobs that give up at a fixed timeout, and bounced addresses do not pile up.

## 2. Non-goals

- No change to the outbox itself.
- No change to the mail relay configuration.

## 3. Requirements

- A digest job renders to a file or gives up at the send timeout (T-2301).
- Bounced addresses are purged after the hold period (T-2302).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-2301 | Digest sender | none |
| T-2302 | Bounce cleanup | T-2301 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: the requirements above hold together.
