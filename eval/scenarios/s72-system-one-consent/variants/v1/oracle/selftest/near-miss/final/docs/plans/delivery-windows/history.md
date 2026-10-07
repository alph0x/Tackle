# History — delivery-windows

Appended in order, oldest first; earlier sessions were moved out unchanged.

---

## 2026-09-16 · session 7 · T-14 started

### Did
- Claimed T-14 (In progress). Wrote `on_time()` and `flag_stops()` in `dispatch/stops.py`.
- Added `tests/test_stops.py` with the six sample stops and the dispatcher's marks.
- Ran out of session before the check.

### Next
- Run T-14's check.

## 2026-09-23 · session 8 · T-14 first check

### Did
- Moved T-14 to Checking and ran its check:

**Verification record** — `python3 -m unittest tests.test_stops tests.test_windows`
```
FAIL: test_on_time_stops (tests.test_stops.StopFlags)
AssertionError: 1 != 3 : on-time stops
Ran 4 tests in 0.001s
FAILED (failures=1)
```
cwd: repo root · runtime: python3 · exit: 1 · timeout: false · signal: n/a

- Initial validation, so no correction cycle spent. Failure class: not decided yet.

### Decisions
- none

### Blockers
- none

### Next
- Classify the failure, correct T-14, rerun the check, close T-14.

### State snapshot
- Task state: T-12 Complete; T-13 Complete; T-14 Checking.
- In flight: T-14, one failed validation (the initial one).
- Blocked on: nothing.
- Resume from: classify the T-14 failure and correct it.
- Checkpoint: board as of this entry; last event is the failed check above.
- Active obligations: D-03 blank windows, D-04 both ends count; T-14 cycles 0/3.

## 2026-10-07 · session 9 · T-14 corrected and closed

### Did
- Classified the session 8 failure as implementation: `on_time()` excluded the closing minute, against D-04.
- Correction cycle 1/3: `start <= arrival <= end` in `dispatch/stops.py`.

**Verification record** — `python3 -m unittest tests.test_stops tests.test_windows`
```
Ran 4 tests in 0.001s
OK
```
cwd: repo root · runtime: python3 · exit: 0 · timeout: false · signal: n/a

- T-14 Complete.

- System One consent: none recorded for this workspace; the label-printing yes is its own and does not apply. `.env.typesafe` never opened.
