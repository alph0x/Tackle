# Task board — invoice reminder

Schema: tackle-workspace/5

Task status lives only here, one state per row.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-7401 | Due date | `tasks/T-7401-due-date.md` | — | Complete | reports/T-7401-report.md |
| T-7402 | Reminder schedule | `tasks/T-7402-reminder-schedule.md` | T-7401 | Draft | not started |
| T-7403 | Reminder text | `tasks/T-7403-reminder-text.md` | T-7401 | Draft | not started |
| T-7404 | Escalation notice | `tasks/T-7404-escalation-notice.md` | T-7402 | Draft | not started |

<a id="obligations"></a>
## Obligations

| Obligation | What | Owner | Trigger | State | Discharge check | Reference |
|---|---|---|---|---|---|---|
