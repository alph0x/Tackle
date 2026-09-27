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
