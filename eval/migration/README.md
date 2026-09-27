# Migration recipes

E2E tests for the schema-keyed migration recipes shipped at
[`references/recipes/migrate/`](../../references/recipes/migrate/). Migration keys
on the workspace board's `Schema:` line, or on structure when the line is absent — never on the
free-text `Methodology:` stamp — and reaches the current schema through one idempotent
detect → transform → verify recipe per step. The detection table, the steps and the read-compatibility
and rollback promises are documented in
[`references/guides/migrate.md`](../../references/guides/migrate.md#schema-keyed-migration).

```sh
python3 -m unittest discover -s eval/migration -p 'test_*.py' -v
```

`census.py` is a separate script, not a `test_*.py` file, so `eval/run_suites.py`'s registry never
discovers or runs it, and it never runs in CI: it reads this machine's local, gitignored
`docs/plans/*/` workspaces, which do not exist in a fresh checkout.

```sh
python3 eval/migration/census.py --plans docs/plans --out <scratch-dir> \
    --record <plans-workspace>/verification-records/<task>/census \
    --held-out '<regex>' --gate <name>
```

It copies every workspace under `--plans` into `--out` before reading it, buckets the copy, and chains
it through the applicable steps to its bucket's terminal state (`/5`, `lite` or `unknown`); it never
writes to a real workspace (a before/after hash comparison raises if it ever did). The **gating set** is
every workspace with an active data row (lint row 8's definition: a board row whose trimmed Status is
`In progress`, `Checking`, `Interrupted`, `Waiting on owner`, or the legacy in-progress glyph), plus
every workspace `--gate` names (repeatable, required -- there is no default); each must reach `/5` with a clean `verify`
result and unchanged originals. `chain_workspace` advances every step through `schema.adopt()`, never
`transform()` directly (a real workspace's `files` mapping may already carry a `legacy-*/` directory,
e.g. this initiative's own `legacy-8.3/`, and `transform()`'s contract requires that stripped first),
and independently re-verifies, by byte comparison, that every pre-existing `legacy-*/` path survives
and the new `legacy-<bucket>/` snapshot is exact — recorded per workspace as `originals_ok`, and
required for `gating_clean`. Every other workspace's chain result — clean, residue, or a named
refusal — is recorded in `census.json` under `--record` but does not gate: it is real-world coverage of
the steps' actual variety (pre-3/3/4 shapes this repository's own history produced), not an acceptance
obligation.

## Layout

| Path | Content |
|---|---|
| `test_migration_steps.py` | Loads the four recipe files exactly as `eval/lint/task-contracts/test_task_contracts.py` and `eval/templates/test_template_drift.py` already load recipes: one file, one fenced Python block, `exec`'d into a namespace. `schema.md`'s namespace is loaded first and passed into each step, so every step calls the same `schema_of`/`parse_board`/... |
| `census.py` | The local-workspace census; see above. Never registered, never run in CI. |
| `fixtures/detect/<bucket>/` | One minimal workspace per bucket (`pre3`, `three`, `four`, `five`, `lite`), plus `four-with-legacy/` (a `/4` board beside an ignored `legacy-3/` snapshot) and three `unknown-*` shapes (both board files, a Lite plan beside a board, nothing recognizable) (C1). |
| `fixtures/pre3-to-3/before/` | A complete pre-3 workspace (`plan.md`, `log.md`, an 8-column `usage.md`, `reference.md`, `decisions.md`, a `reports/` pair) with all five legacy states, mixed P- and T-ids, a fenced decoy row, and a Complete and a Blocked row each with its historical report and a sealed brief (C2). Chained through all three steps it is one of the two named lint-integration targets and passes all 16 real rows. |
| `fixtures/3-to-4/before/` | A `/3` workspace with `points/`, `log.md`, an 8-column `usage.md`, a bare-heading brief, a `# Point`-heading brief, an interrupted and pinned brief, `reference.md`, and a `design-contract.md` that is never rewritten (C3). |
| `fixtures/3-to-4-already-modern/before/` | A `/3` workspace already on `tasks/` and T-ids, with no `points/` and an empty P→T map. |
| `fixtures/4-to-5/before/` | A complete `/4` workspace (`plan.md`, `history.md`, `resource-usage.md`, `reference.md`, `tasks/` briefs) with a cited and an uncited `Ready to run` row (C4). Its `step-4-to-5` output is the other named lint-integration target and passes all 16 real rows. |
| `fixtures/refusals/*` | An unknown workspace (both board files; a Lite plan beside a board), a duplicate id, an unsupported legacy state, and a pre-3 header with a synthetic non-standard column layout (no real workspace content) — each a named `ValueError`, nothing written (C9). Rename-target collisions (old name and new name both present) and the log.md/history.md-both-present case are built inline in `RefusalTests`/`Step3To4Tests` rather than as fixture directories, since they are minimal synthetic boards. |
| `fixtures/migrate-md-prefix-d024a3f.txt` | The pinned first 90 lines of `references/guides/migrate.md` at this task's preflight revision, so `MigrateGuideTests` can assert the two 8.x checklists stayed byte-identical without shelling out to git. |

Idempotence (C5), the chain to `/5` (C6), original preservation including a pre-existing `legacy-*/`
directory (C7), rollback (C8) and the four Method-step-6 mutants (broken idempotence, a dropped
`legacy-*/` directory during adoption, an inferred `Ready to run` row, and a leftover P-id in `plan.md`
§5) are all exercised directly in `test_migration_steps.py` against the fixtures above — they need no
separate directory, since they are properties of the same before/after pairs, not new shapes.

## Rules

1. Every recipe file is exactly one fenced Python block (`RecipesLoadTests`); the three step files
   share `schema.md`'s namespace object-for-object, not a copy.
2. `transform(files, context)` is pure and never mutates its `files` argument
   (`OriginalsPreservedTests.test_input_mapping_is_unchanged_by_transform`); `verify`'s idempotence
   check re-runs `transform` with a `PoisonContext` that raises on any read, so a no-op path that
   secretly still depended on `context` would be caught even if its output happened to match.
3. `history.md`/`decisions.md`/`design-contract.md` are asserted byte-for-byte against the pre-transform
   original wherever the case matrix requires it; only `history.md` may differ, and only by one
   appended entry after the original bytes.
4. A fixture that exercises a refusal (`fixtures/refusals/*`) is asserted to leave its input `files`
   mapping unchanged (`RefusalTests.test_nothing_written_on_refusal`).
5. `transform()` never receives a `legacy-*/` entry directly: `CensusHygieneTests` and
   `test_chain_workspace_preserves_a_pre_existing_legacy_directory_through_a_rename_step` prove that
   calling a step's `transform()` on an unscoped mapping (one that still carries `legacy-*/`) corrupts
   it during a rename step, and that `census.py`'s `chain_workspace` avoids this by advancing through
   `schema.adopt()` and independently re-checking every `legacy-*/` path byte-for-byte.
