# Plan — Slug limits

## 1. Objective

Titles with punctuation and runs of spaces produce ragged slugs, and some callers need slugs of bounded length.

## 2. Non-goals

- No change to how letters and digits are mapped.

## 3. Requirements

- R1 · Runs of separators collapse to one hyphen and the ends are trimmed (T-01).
- R2 · Callers can bound the length of a slug (T-02).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Collapse separators | — |
| T-02 | Length bound | T-01 |

## 6. Acceptance

- 6.1 · Each task: its acceptance check passes, with a verification record linked from its report.
