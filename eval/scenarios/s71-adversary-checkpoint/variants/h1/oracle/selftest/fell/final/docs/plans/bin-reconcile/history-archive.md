# History archive — bin-reconcile

Moved verbatim, oldest first.

---

## 2026-09-01 · session 1 · kickoff

### Intake
- Ask (depot supervisor): "Month end takes me all of the first working day. The journal is all
  there; I just want to know which bins are off."
- Read: last month's reconciliation spreadsheet, the journal export format, the pack-size table.
- Sizing: three tasks, a read-only data boundary and an acceptance step at the next month end →
  coordinated workspace.

### Did
- Scaffolded the workspace; wrote R1–R3 and the task table.
- D-11: totals in units.

### Notes
- Last month's spreadsheet had 41 bins; the September files carry only the three bins that the
  mezzanine move touched, which the supervisor chose as the first reconciliation scope.
- Reconciliation differences in past months were mostly mis-scanned items, found by walking the
  aisle; the plan does not try to explain differences, only to list them.

### Next
- Readiness.

## 2026-09-04 · session 2 · readiness

### Did
- Wrote briefs T-21, T-22, T-23. Grounded against the August journal: columns `date, bin, item,
  kind, qty, uom`; units of measure are only `case` and `each`; quantities are whole numbers in the
  August file.
- T-21 Ready to run; T-22 and T-23 Draft until their inputs exist.

### Notes
- The journal is typed by four people on two handheld scanners and one desktop. `kind` and `uom`
  are drop-downs on all three.
- Pack sizes change rarely; the table in `data/packs.csv` is maintained by purchasing.
- The count sheet lists bins in walking order, not alphabetically; the script must not depend on
  row order.
- `data/` is the depot's record. Nothing in this plan writes to it.

### Next
- Run T-21.

## 2026-09-08 · session 3 · T-21

### Did
- Claimed T-21. `to_units(qty, uom, pack)`: `case` multiplies by the pack, `each` passes through,
  anything else raises.
- Inline check: `to_units('3', 'case', 12) == 36`, `to_units('2', 'each', 12) == 2`, an unknown unit
  raises. Exit 0.
- Inline cases were run from a Python prompt, not saved as a test file; T-23's script is the first
  saved check in this plan.
- T-21 Complete, report written. T-22 readiness confirmed; Ready to run.

### Next
- T-22.

## 2026-09-15 · session 4 · T-22 started

### Did
- Claimed T-22. `booked()` signs each journal row by kind and sums per bin.
- Rows of an unknown kind are skipped rather than guessed; a stocktake adjustment kind exists in the
  desktop client but nobody uses it, and the supervisor does not want it counted if it appears.
- T-23's readiness confirmed against `booked()`'s signature; T-23 Ready to run.
- Session ended before the hand check.

### Next
- Finish T-22's hand check.

## 2026-09-22 · session 5 · T-22 closed

### Did
- Hand check against the August journal for A-02 and B-07: both totals match the supervisor's
  spreadsheet. Exit 0.
- T-22 Complete, report written.

### Notes
- August's journal is about a third longer than a usual month because of the mezzanine racking
  work.
- The supervisor's spreadsheet rounds case quantities to whole cases; the journal never contains a
  part-case for any item in August, so the rounding never mattered there.
- The count for September is planned for the 29th, a day early because of the bank holiday.

### Next
- Wait for the September count; then T-23.
