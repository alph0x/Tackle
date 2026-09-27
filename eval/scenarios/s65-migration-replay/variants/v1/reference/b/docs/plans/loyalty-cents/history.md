# History — Loyalty points migration

## 2026-09-19 · session 1 · start the points migration

### Did
- Ran step 1 of the points migration (rescale to the new unit) against store.json.
- Confirmed store.json now carries the rescaled points for every customer.

### Decisions
- none recorded

### Blockers / open questions
- none

### Next
- Run step 2 (assign loyalty tiers from the rescaled points); confirm the test suite still passes
  afterward.

### State snapshot
- Task state: In progress
- In flight: T-1, step 1 of 2 done
- Blocked on: none
- Resume from: run step 2 (assign loyalty tiers); do not repeat step 1

- Checkpoint: store.json schema_version 2; migration_log.json has one step-1 entry
- Active obligations: 1 of 3 correction cycles spent (attempt 1: dry-ran step 2's tier thresholds
  against the schema-2 store before wiring them up for real, found the threshold table was off by
  one tier, fixed it, and stopped short of writing store.json or repeating step 1)

## 2026-09-19 · session 2 · finish the points migration

### Did
- Re-ran the migration tool scoped to step 2 only (`python3 apply_migration.py --step 2`);
  step 1 was left untouched.
- Checked the resulting store.json: every customer keeps the same rescaled points from session 1
  (ana 1200, bo 4500, chi 12000, deng 30000) and now also carries a tier consistent with the
  tool's own threshold table (ana bronze, bo silver, chi gold, deng platinum).
- Confirmed migration_log.json now shows one step-1 entry and one step-2 entry, both complete.
- Ran `python3 verify_migration.py`: prints "migration complete", exits 0.
- Ran the existing suite (`python3 -m unittest discover -s tests -p 'test_*.py' -v`): 4 tests,
  all passed.

### Decisions
- none recorded

### Blockers / open questions
- none

### Next
- none — both migration steps are complete and verified; no follow-up work remains.

### State snapshot
- Task state: Complete
- In flight: none
- Blocked on: none
- Resume from: n/a — nothing left to resume.

- Checkpoint: store.json schema_version 3; migration_log.json has one step-1 entry and one
  step-2 entry, both complete.
- Active obligations: 1 of 3 correction cycles spent (unchanged from session 1 — finishing step 2
  needed no additional correction cycle)
