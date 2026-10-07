# History archive — delivery-windows

Sessions moved here verbatim, oldest first.

---

## 2026-08-24 · session 1 · kickoff

### Intake
- Ask (depot lead, by phone): "Our dispatcher reads tomorrow's run sheet against the customers' windows
  every evening and still misses some. Can the export do that for us?"
- Looked at: one run-sheet export (CSV, 96 stops), the depot's service agreement, the dispatcher's
  marked-up printout from the week before.
- Sizing: three tasks, one policy question about the closing minute, an acceptance step with the
  dispatcher → a coordinated workspace.

### Did
- Scaffolded the workspace; wrote R1–R3.
- Opened Q-02: is a stop that arrives at the closing minute on time?

### Notes
- The export has one window column, `HH:MM-HH:MM`, written by the depot terminal; it cannot be changed.
- Business customers often leave the window blank.

### Next
- Wait for Q-02, then readiness.

## 2026-08-26 · session 2 · readiness

### Did
- Recorded D-03: blank windows get `no window`.
- Briefs T-12, T-13, T-14 written. Grounded against the export: windows are always zero-padded.
- T-12 Ready to run. T-14 Draft until the reader exists.

### Notes
- The marked-up printout has 11 stops flagged by hand; two of them were wrong by the dispatcher's own
  later account, both stops arriving exactly at closing time.

### Next
- Run T-12.

## 2026-08-28 · session 3 · T-12

### Did
- Claimed T-12. `parse_window` splits on the dash and returns None for anything it cannot read.

**Verification record** — `python3 -m unittest tests.test_windows`
```
..
Ran 2 tests in 0.001s
OK
```
cwd: repo root · runtime: python3 · exit: 0 · timeout: false · signal: n/a

- T-12 Complete; report written.

### Next
- Q-02 is still open; T-13.

## 2026-09-02 · session 4 · Q-02 answered

### Did
- Depot lead answered Q-02: both ends count ("between 09:00 and 11:00 inclusive" in the agreement).
  Recorded as D-04; Q-02 resolved.
- No code.

### Next
- T-13 with the dispatcher; then T-14.

## 2026-09-04 · session 5 · T-14 readiness

### Did
- T-14 readiness confirmed against `parse_window`; T-14 Ready to run.
- Asked the dispatcher for one evening's sheet with her own marks for acceptance 6.2; she will keep the
  18 September one.

### Next
- T-13 at the terminal.

## 2026-09-09 · session 6 · T-13 at the terminal

### Did
- Sat with the dispatcher. She exported the 18 September run sheet by following the notes; T-13 Complete.
- Took six stops from that sheet as T-14's test sample, with her marks: three on time, one late, one
  early, one with no window.

### Notes
- She sorts the sheet by van, not by time; the flags must stay one row per stop.
- The depot has two vans on the eastern loop; both appear in the same export.

### Next
- Start T-14.
