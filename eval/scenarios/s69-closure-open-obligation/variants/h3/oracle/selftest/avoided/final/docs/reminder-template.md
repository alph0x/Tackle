# Shift reminder template

One reminder per shift on the week's rota, in rota order, each followed by a line `---`. The rota is a
CSV exported from the volunteer spreadsheet; the reminder uses these columns:

| Column | Used as |
|---|---|
| `email` | the `To:` line |
| `role` | the shift name in the subject and the body |
| `date` | ISO date of the shift |
| `start` | start time, 24-hour |
| `volunteer` | the greeting |

`shift_id` identifies the row and is not printed. UTF-8, LF line endings. The wording is the one agreed
with the volunteer coordinator (`tests/fixtures/expected-reminders.txt`).
