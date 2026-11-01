# Plan — Parcel reports

## 1. Objective

Make the parcel loader handle empty input and preserve working report consumers.

## 2. Non-goals

- No public helper rename without an owner decision.

## 3. Requirements

- Empty input returns no rows and the report counts parcel rows.

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-4401 | Parcel loader correction | — |

## 6. Acceptance

- Each task's acceptance commands succeed.
