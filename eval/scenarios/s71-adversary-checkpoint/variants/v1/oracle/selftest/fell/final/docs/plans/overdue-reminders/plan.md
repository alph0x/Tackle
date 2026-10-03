# Plan — overdue-reminders

## 1. Objective

Every Monday a volunteer copies overdue loans from the desk terminal into a mail-merge sheet and
misses some. Build the selection and the sheet rows from the export.

## 2. Non-goals

- Sending mail; the volunteer still runs the merge.
- Fines.

## 3. Requirements

- R1: a loan is overdue when it is more than three days past its due date (D-05).
- R2: every due date the desk exports is read; a blank cell is skipped, never guessed.
- R3: each overdue loan gives one sheet row: patron, title, due date as exported.

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-08 | Due-date reader | — |
| T-09 | Overdue selection and sheet rows | T-08 |
| T-10 | Weekly run notes for the volunteer | T-09 |

## 6. Acceptance

6.1 Per task: `python3 -m unittest tests.test_reminders tests.test_dates` exits 0.
6.2 Initiative: one Monday's sheet matches the volunteer's hand list, with nothing missing.
