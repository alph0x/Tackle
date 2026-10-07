# pantry-tools

Small tools for the Harbourside Food Pantry's volunteer team.

- `python3 -m reminders week <shifts.csv> <out.txt>` writes the week's shift reminders, one per shift,
  ready for the coordinator to paste into the mail tool.
- Template: `docs/reminder-template.md`. Tests: `python3 -m unittest discover -s tests -q`.
- Acceptance of the reminder work: `sh checks/accept.sh`.

Planning: `docs/plans/shift-reminders/`.
