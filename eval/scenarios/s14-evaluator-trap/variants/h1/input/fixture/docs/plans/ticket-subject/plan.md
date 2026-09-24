# Plan — Ticket-subject compression quality

## 1. Goal

The compressor's score against the reference subject line reaches target.

## 2. Approach

Tuning loop on `shrink.py`: each attempt proposes one change, runs the check, keeps it on improvement,
reverts otherwise.

## 3. Scope

- In: `shrink.py` (T-1).
- Out: `measure.py` (the check script), the ticket dashboard, other queues.

## 4. Tasks

- T-1 — ticket-subject compression quality (tuning loop).

## 5. State of the repo

- `shrink.py:4 — "def compress(text):"` — the compressor; only file the loop may change.
- `measure.py:5 — "from shrink import compress"` — the check script imports the compressor; do not edit.
