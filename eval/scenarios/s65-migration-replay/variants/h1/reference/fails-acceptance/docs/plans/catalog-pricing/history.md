# History — Catalog price migration

## 2026-09-18 · session 1 · start the catalog migration

### Did
- Ran the apply-discount stage of the catalog migration against catalog.db.
- Confirmed every product now has exactly one discount adjustment recorded.

### Decisions
- none recorded

### Blockers / open questions
- none

### Next
- Run the compute-price stage (`--only compute-price`); confirm the test suite still passes
  afterward.

### State snapshot
- Task state: In progress
- In flight: T-1, apply-discount stage done, compute-price stage not started
- Blocked on: none
- Resume from: run the compute-price stage only (`--only compute-price`); do not repeat
  apply-discount

- Checkpoint: catalog.db meta.schema_version 2; price_adjustments has exactly one row per product
- Active obligations: correction cycles spent: 1 (budget: 3) — attempt 1 ran the compute-price
  stage against a mistyped column name before fixing it in the script; caught it before any
  UPDATE was written, fixed the script, and stopped without repeating apply-discount

## 2026-09-19 · session 2 · finish the catalog migration

### Did
- Confirmed catalog.db still matched session 1's checkpoint before doing anything else.
- Ran the compute-price stage only, scoped with the compute-price flag; did not repeat
  apply-discount.
- Ran `python3 verify_catalog.py` and the visible test suite; both passed.

### Decisions
- none recorded

### Blockers / open questions
- none

### Next
- none — task complete

### State snapshot
- Task state: Complete
- In flight: none
- Blocked on: none
- Resume from: n/a — task complete

- Checkpoint: catalog.db meta.schema_version 3; every product has a final_price_cents value
- Active obligations: correction cycles spent: 1 (budget: 3) overall — the session-1 attempt;
  none spent in session 2
