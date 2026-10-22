# Plan — Invoice reminders

## 1. Objective

Remind customers about unpaid invoices before they fall due.

## 2. Non-goals

- No change to the invoicing system the invoices come from.

## 3. Requirements

- Requirement A · The due date works as its brief states (T-7401).
- Requirement B · The reminder schedule works as its brief states (T-7402).
- Requirement C · The reminder text works as its brief states (T-7403).
- Requirement D · The escalation notice works as its brief states (T-7404).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-7401 | Due date | — |
| T-7402 | Reminder schedule | T-7401 |
| T-7403 | Reminder text | T-7401 |
| T-7404 | Escalation notice | T-7402 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
- 6.3 · Readiness: the project validator prints nothing for the open briefs before they are handed out.
