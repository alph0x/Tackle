# Plan — notes cleanup

## 1. Objective

The changes file mixes entries, indented entries and comments; the notes should hold every entry.

## 2. Non-goals

- No change to the bullet format.

## 3. Requirements

- R1 · An entry becomes `- **type**: text` (T-01).
- R2 · Lines that are not `type: text` entries are not bullets (T-02).
- R3 · Entries indented with spaces or tabs are entries too (T-03).

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-01 | Bullet format | — |
| T-02 | Type filter | T-01 |
| T-03 | Indented entries | T-02 |

## 6. Acceptance

- 6.1 · Each task: `sh tests/run.sh` exits 0, with a verification record linked from its report.
- 6.2 · Initiative: a changes file with indented entries and comments yields every entry once.
