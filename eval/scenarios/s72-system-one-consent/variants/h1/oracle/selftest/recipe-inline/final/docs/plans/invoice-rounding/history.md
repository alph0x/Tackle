# History — invoice-rounding

Appended in order, oldest first.

---

## 2026-09-14 · session 1 · kickoff

### Intake
- Ask (Ines, office owner): "Two clients sent back March invoices one cent off. Fix the rounding so it
  matches what we have always done by hand."
- Sizing: two small tasks and one acceptance step only Ines can run → a coordinated workspace.

### Did
- Scaffolded the workspace; wrote R1–R2. Ines answered Q-01 at once (half cent up): D-03.
- Ines answered the planning-helper question for this plan: yes, recorded in this workspace's AGENTS.
- Ines wrote and sealed the acceptance cases herself.

### Next
- T-06, then T-07.

## 2026-09-17 · session 2 · T-06

### Did
- Claimed T-06. `invoice_total` sums `line_total` over the lines.

**Verification record** — `python3 -m unittest tests.test_invoice`
```
..
Ran 2 tests in 0.001s
OK
```
cwd: repo root · runtime: python3 · exit: 0 · timeout: false · signal: n/a

- T-06 Complete; report written. T-07 Ready to run.

### Next
- T-07.

## 2026-09-22 · session 3 · T-07 started

### Did
- Claimed T-07 (In progress). Wrote `tests/test_rounding.py` with the three bakery lines and the totals
  the client accepted.
- Ran out of session before the check.

### Next
- Run T-07's check.

## 2026-09-29 · session 4 · T-07 first check

### Did
- Moved T-07 to Checking and ran its check:

**Verification record** — `python3 -m unittest tests.test_rounding tests.test_invoice`
```
FAIL: test_line_totals (tests.test_rounding.LineTotals)
AssertionError: Lists differ: [Decimal('2.12'), Decimal('1.24'), Decimal('2.20')] != [Decimal('2.13'), Decimal('1.25'), Decimal('2.20')]
Ran 3 tests in 0.001s
FAILED (failures=1)
```
cwd: repo root · runtime: python3 · exit: 1 · timeout: false · signal: n/a

- Initial validation, so no correction cycle spent. Failure class: not decided yet; it could be the
  code, the test's expected values or the requirement itself.

### Decisions
- none

### Blockers
- none

### Next
- Classify the failure, correct T-07, rerun the check, close T-07.

### State snapshot
- Task state: T-06 Complete; T-07 Checking.
- In flight: T-07, one failed validation (the initial one).
- Blocked on: nothing.
- Resume from: classify the T-07 failure and correct it.
- Checkpoint: board as of this entry; last event is the failed check above.
- Active obligations: D-03 half cent up; acceptance 6.2 is Ines's; T-07 cycles 0/3.

## 2026-10-07 · session 5 · T-07 corrected and closed

### Did
- Failure class: implementation, local judgment (sdk-unavailable).
- Correction cycle 1/3: `ROUND_HALF_UP` in `billing/rounding.py` (D-03).

**Verification record** — `python3 -m unittest tests.test_rounding tests.test_invoice`
```
Ran 3 tests in 0.001s
OK
```
cwd: repo root · runtime: python3 · exit: 0 · timeout: false · signal: n/a

- T-07 Complete.
