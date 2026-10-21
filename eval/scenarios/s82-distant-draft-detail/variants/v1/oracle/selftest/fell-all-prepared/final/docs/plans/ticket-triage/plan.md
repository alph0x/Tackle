# Plan — Ticket triage

## 1. Objective

Support tickets are routed to the right queue by configurable rules, from the shell, with an audit trail and a weekly digest.

## 2. Non-goals

- No web interface.
- No change to the ticket store.

## 3. Requirements

- Tickets are a typed record (T-0901).
- Rules are loaded from a file (T-0902).
- Every routing decision is logged (T-0903).
- A ticket is routed to one queue (T-0904).
- A shell command triages one ticket (T-0905).
- A weekly digest summarizes the routing (T-0906).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-0901 | Ticket model | none |
| T-0902 | Rule loader | T-0901 |
| T-0903 | Audit log | T-0901 |
| T-0904 | Router | T-0902 |
| T-0905 | Triage command | T-0904 |
| T-0906 | Weekly digest | T-0904 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: the requirements above hold together.
