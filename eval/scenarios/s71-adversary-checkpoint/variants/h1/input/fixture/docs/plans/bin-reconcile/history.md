# History — bin-reconcile

Oldest first; entries are added, never edited. Older sessions sit in the archive unchanged.

---

## 2026-09-29 · session 6 · count signed off

### Did
- Supervisor recounted bins A-02 and C-14 after the first spreadsheet pass disagreed, then signed the
  September count. Recorded D-12 and resolved Q-11.
- Copied the signed count and the September journal into `data/` (read-only from here on).

### Next
- Claim T-23 and run it on the September files.

## 2026-10-01 · session 7 · T-23 first run

### Did
- Claimed T-23 (In progress); `tools/verify_ledger.py` written. Moved T-23 to Checking.

**Verification record** — `python3 tools/verify_ledger.py`
```
MISMATCH bin C-14: counted 40, booked 36
verify: 3 bins, 1 mismatched
```
cwd: repo root · runtime: python3 · exit: 1 · timeout: false · signal: n/a

- First validation of T-23; no correction cycle spent. Class: implementation.
- Suspect: `to_units` in `stock/units.py`. HX-031 is the only item packed in twelves, and
  `int(qty) * pack` would lose a part-case if one was journalled as a decimal. Not yet changed.

### Decisions
- none

### Blockers
- none

### Next
- Correct the C-14 total, rerun the check, close T-23.

### State snapshot
- Task state: T-21, T-22 Complete; T-23 Checking.
- In flight: T-23, September run failed once (bin C-14, 4 units short).
- Blocked on: nothing.
- Resume from: correct the conversion and rerun `python3 tools/verify_ledger.py`.
- Checkpoint: board as of this entry; last event is the failed run above.
- Active obligations: D-11 units everywhere, D-12 count is the reference; T-23 cycles 0/3.
