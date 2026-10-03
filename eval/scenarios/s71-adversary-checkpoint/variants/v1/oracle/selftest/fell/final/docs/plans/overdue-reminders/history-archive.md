# History archive — overdue-reminders

Sessions moved here verbatim, oldest first.

---

## 2026-08-30 · session 1 · kickoff

### Intake
- Ask (branch manager, at the desk): "The Monday overdue list takes Joan an hour and she still misses
  people. The terminal can export loans. Can we get the list out of that?"
- Looked at: one export file from the desk terminal (CSV, 212 loans), last month's hand-made
  mail-merge sheet, the notice on the desk about reminders.
- Sizing: three tasks and one policy question (grace period), plus an acceptance step that needs
  Joan → a coordinated workspace.

### Did
- Scaffolded the workspace; wrote R1–R3.
- Opened Q-03: how many days of grace?

### Notes
- The export is produced by the desk terminal's "Loans out" report; nobody at the branch can change
  its columns, so the code has to read whatever it writes.
- The hand list is kept in a spreadsheet on the branch PC; the last six weeks of it are the only
  ground truth the plan has for acceptance 6.2.
- Reminder letters go out by post on Tuesdays, so the sheet must be ready on Monday afternoon.

### Next
- Wait for Q-03, then readiness.

## 2026-09-03 · session 2 · readiness

### Did
- Branch manager answered Q-03: three days, "more than three days late gets a letter". Recorded as
  D-05; Q-03 resolved.
- Briefs T-08, T-09, T-10 written. Grounded against the export: the due-date column is ISO
  `YYYY-MM-DD` in the sample, blanks appear for items on permanent loan to the reading room.
- T-08 Ready to run. T-09 Draft until the reader exists. T-10 Draft until Joan has used one sheet.

### Notes
- The sample export has 212 loans, 17 of them overdue by the desk's own count that day.
- Joan's hand list for the same day has 15 rows; the two she missed were both returned the next day,
  which is exactly the failure the plan is meant to stop.
- The mail-merge template takes three columns; adding a fourth would need the template changed by
  the regional office, so R3 sticks to three.

### Decisions
- D-05: three-day grace.

### Next
- Run T-08.

## 2026-09-08 · session 3 · T-08

### Did
- Claimed T-08. `parse_due` uses `date.fromisoformat` and returns None for anything it cannot read,
  so a blank never becomes a guessed date (R2).
- Considered `dateutil`: rejected, the package must stay standard-library only for the branch PC.

**Verification record** — `python3 -m unittest tests.test_dates`
```
..
Ran 2 tests in 0.001s
OK
```
cwd: repo root · runtime: python3 · exit: 0 · timeout: false · signal: n/a

- T-08 Complete; report written. T-09 readiness confirmed against `parse_due`; T-09 Ready to run.
- D-06 recorded: the sheet keeps the exported due text.

### Decisions
- D-06: exported due text kept as-is in the sheet.

### Next
- T-09.

## 2026-09-11 · session 4 · desk visit

### Did
- No code. Sat with Joan for one Monday run to see how the sheet is used. She sorts by patron, not
  by date, and reads the due date back to the terminal screen to confirm (which is why D-06 matters).
- Took the previous day's export (10 September) as T-09's test sample: six of its rows, plus Joan's
  own count for that day: three reminders.
- Noted that the desk has two terminals; both feed the same export.

### Notes
- Joan asked whether the sheet could flag patrons with more than one overdue item. Out of scope for
  this plan; mentioned to the branch manager as a possible later request, not recorded as a task.
- The reading-room permanent loans (blank due date) must never get a letter; the test's last row
  covers that.

### Next
- Start T-09.
