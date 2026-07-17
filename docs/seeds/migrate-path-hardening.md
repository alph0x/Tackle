# Seed — Migrate-path hardening initiative (not yet planned)

**Status:** SHIPPED in 3.4.0 (initiative `docs/plans/tackle-migrate-hardening/`; dogfood proof in `docs/plans/tackle-2.0/`). Evidence artifact preserved: pristine backup in `docs/seeds/tackle-2.0-pristine-backup/`. Original seed content follows for the record.

## Origin

User question 2026-07-17: "does 3.3.0 migrate old plans well?" Tested by migrating `tackle-2.0` → 3.3.0 on a copy. Answer: NO — checklist chain covers rule adoption but not structural conformance; migrated workspace still fails lint rows 1, 2, 5.

## Findings (all evidenced in the test)

1. **No v3.0→v3.1 checklist** — 3.1.0 execution discipline (INTENT gate, retry bound, two-halves verification) is never adopted by migrated plans.
2. **Artifact renames uncovered** — `contract.md` → `design-contract.md` (+50 reference updates) done by hand; no item mentions renames (`context.md`, `strategy.md`, `snapshots/` mapping undocumented too).
3. **Lint row 2 vs old structure** — 2.0-era plan.md has no point table; no checklist item creates the P-xx id list row 2 requires.
4. **Lint row 5 vs per-point Status fields** — 2.0 points carry `**Status**: 🟢 done`; item 1 of v2.0→v2.1 only moves the plan.md column.
5. **Lint row 1 false positive** — old points legitimately grep for `{{placeholders}}` in done-signals; row 1 needs an exemption for command content (or migration must quote them).
6. **Unanchored old citations escape row 4** — never verified, never marked; needs a git-historical citation policy (invented during tackle-model-teams execution, not yet documented).
7. **Non-uniform wiring lines** — "add Traces to under Status & wiring" is not mechanically executable across 2.0 point formats.
8. **Status vocabulary lacks "skipped/won't-do"** — real plans skip optional slices; 🔴🟡⏸🟢 can't express it (migration mapped ⚪→🟢 by judgment).
9. **Archival track missing** — migrate step 3 says "scope to forward-looking work" but no checklist operationalizes it for fully-done plans (re-grounding, evidence retrofits, seals are theater on closed work).

## Candidate scope (to size at intake)

- migrate.md: add v3.0→v3.1 checklist; add renames item; add structural-conformance items (plan.md id list, per-point Status removal); add archival-track variant for done plans; document git-historical citation form.
- lint-spec.md: row 1 exemption for quoted command content; row 8 already hardened (docs/plans invariant, 3.3.0).
- Decide: add ⚪ skipped to status vocabulary (board-only) or keep 4-value vocab + mapping rule.
- Possibly a small fix to row 2 (accept board.md as the id source for old plans).
