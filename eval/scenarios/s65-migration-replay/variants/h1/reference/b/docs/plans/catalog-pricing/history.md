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

## 2026-09-18 · session 2 · finish the catalog migration

### Did
- Re-ran the migration tool scoped to the compute-price stage only
  (`python3 run_catalog_migration.py --only compute-price`); left apply-discount untouched.
- Checked catalog.db: price_adjustments still holds exactly one row per product (no second
  discount round), and every product now has a final_price_cents computed once from its base
  price and that single adjustment — widget 900, gadget 1800, gizmo 4500, doohickey 7200.
- Confirmed meta.schema_version now reads 3.
- Ran `python3 verify_catalog.py`: prints "migration complete", exits 0.
- Ran the existing suite (`python3 -m unittest discover -s tests -p 'test_*.py' -v`): 3 tests,
  all passed.

### Decisions
- none recorded

### Blockers / open questions
- none

### Next
- none — the catalog migration is complete and verified; no follow-up work remains.

### State snapshot
- Task state: Complete
- In flight: none
- Blocked on: none
- Resume from: n/a — nothing left to resume.

- Checkpoint: catalog.db meta.schema_version 3; every product has a final_price_cents computed
  from exactly one discount adjustment.
- Active obligations: correction cycles spent: 1 (budget: 3) — unchanged from session 1; finishing
  the compute-price stage needed no additional correction cycle
