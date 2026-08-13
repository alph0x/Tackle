# Step 8.5 — Migrate

## v5.2 → v5.3 checklist

Run these when migrating a plan created with Tackle 5.2.x:

1. **Note the two-phase drift check** — `ground.md` step 2 is now two-phase; staleness is decided by content, never session memory.
2. **Note `tackle-check ground <workspace>`** — the runner's first writing gate: re-anchors drifted citations in place; lint row 4 names it as the fix path.
3. **Record** — write a `D-xx` in `decisions.md`, append a `log.md` entry, and bump the plan stamp.
