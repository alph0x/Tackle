# Step 8.5 — Migrate

Bring an old plan to the current methodology — a single **full-adoption** track with no archival shortcuts: migration ends when the workspace is fully featured (structurally conformant plus carrying every workspace-level feature), never at a reduced "archival" state, even when the plan's work is all closed.

Generic step 3's forward-looking scope applies to EXECUTION work only: closed points are never re-executed, historical log entries stay untouched (append-only), and execution protocols (INTENT gate, maker/checker, closure reports) bind at the next point execution. The workspace itself — closed work included — conforms structurally in full.

A migrated workspace MUST satisfy the full-adoption contract F-1..F-8; each line names the checklist item that verifies it:

- **F-1 · Agent contract** — `AGENTS.md` carries the Autonomy level, harness map, §Model map with capability line, `agent-messaging` capability row, and current Methodology stamp → v3.2 → v3.3 items 1, 3 and v2.1 → v3.0 items 6, 8.
- **F-2 · Artifact names** — current artifact names only; every rename reference-updated workspace-wide and recorded in `decisions.md` → Artifact renames checklist.
- **F-3 · Status conformance** — `plan.md` lists every P-xx id; `board.md` is the ONLY status source (vocabulary 🔴🟡⏸🟢⚪) → Structural conformance items 1–3.
- **F-4 · Citations** — every `file:line` citation anchored or git-historical; no bare `file lines X–Y` remains → Citations item.
- **F-5 · Point fields** — points with remaining work carry the full current field set (Traces-to, INTENT gate, Autonomy override, anchored Context); done points carry Traces-to minimum → v3.0 → v3.1 items 1–3 and Structural conformance item 4.
- **F-6 · Evidence discipline** — log entries written after migration carry evidence blocks; historical entries stay untouched → v2.1 → v3.0 item 2, applied forward-looking.
- **F-7 · Execution protocols** — `AGENTS.md` names maker/checker, closure report + sign-off, one logical Coordinator with `coordinator.md`, the closure handshake, and the rework bound as binding for any future point execution → v2.1 → v3.0 item 7, v3.0 → v3.1 items 1–2, v3.2 → v3.3 item 2.
- **F-8 · Verification** — `lint: N/N checks passed` on the migrated workspace and the Methodology stamp is current → generic step 6 plus each checklist's record item.

## Generic migration

1. Detect the gap (trust structure, not just the stamp).
2. Preserve what's settled.
3. Scope to forward-looking work.
4. Re-ground remaining points.
5. Add missing artifacts.
6. Lint + checkpoint.
7. Record migration `D-xx` + log entry + bump stamp.

## v4.0 → v4.1 checklist

Run these when migrating a plan created with Tackle 4.0.x:

1. **Note skill self-update** — the installed skill now checks for a new release daily during planning intake (Step 0 "Self-update check") and self-updates via `guides/update.md`; `/tackle-update` forces it. Informational — no workspace edit.
2. **Record** — write a `D-xx` in `decisions.md` noting the version adopted, append a `log.md` entry, and bump the plan stamp.

## v3.4 → v4.0 checklist

Run these when migrating a plan created with Tackle 3.4.x:

1. **Note `Type:` field awareness** — point briefings may declare `Type: standard` (the default when absent), `Type: discovery`, or `Type: experiment`; old points are `standard` by default and need no rewrite.
2. **Audit `Depends-on` edges** — every `Depends-on` line names the crossing artifact (the concrete upstream output the point consumes — a file, a section, a schema, a protocol); a legitimate ordering-only edge is recorded as a `D-xx` waiver, never waived silently, and false edges are cut, not waived.
3. **Consider `Lenses:` adoption** — a high-risk point MAY declare `Lenses:` (distinct verification lenses run as independent skeptic checks, decided by majority vote); absent ⇒ single-checker behavior, unchanged. No workspace edit required.
4. **Add the Confidence column + backfill grades** — `board.md` gains a trailing `Confidence` column; lint row 3 is position-independent (legacy 5-column and graded 6-column boards both pass), so the column's placement is free. Backfill every closed point mechanically: **E1** if a checker evidence block (command + output + exit line from the independent checker) exists in `log.md`/`reports/`, **E3** otherwise — grades are derived from evidence, never judged, and never upgraded without the evidence.
5. **Note the L3 E1-chain condition** — unattended (L3) execution now requires the point's dependency chain to be E1-pure; asserted or review-gated upstream evidence caps the point at L2. Informational — binds at the next L3 execution, no workspace edit.
6. **Note lint rows 9–10** — row 9 checks loop-point budget fields (`Type: discovery` ⇒ `Rounds:`; `Type: experiment` ⇒ `Metric:` + `Threshold:` + `Rounds:`); row 10 checks every 🟢/⏸ board row carries a grade from E1/E2/E3/E0. The new rows apply at the next lint run; row 10 is satisfied by item 4's backfill.
7. **Note plan archetypes** — proven decomposition skeletons (point list, edge pattern, wave shape, trap warnings, provenance) live in `references/archetypes/<name>.md`; when re-planning or adding work, check for a matching archetype. Informational — no workspace edit.
8. **Bump the stamp** — record a `D-xx` in `decisions.md`, append a `log.md` entry, and bump the workspace `Methodology:` stamp to Tackle 4.0.0.

## v3.3 → v3.4 checklist

Run these when migrating a plan created with Tackle 3.3.x:

1. **Adopt the skipped status** — add `⚪ skipped (optional slice not executed, with one-line reason)` to the workspace's status vocabulary references (`AGENTS.md` executor contract, `board.md` legend if present); lint rows 3/5 now accept/scan for it.
2. **Add §Learning intake** — copy the §Learning intake section from `AGENTS.tmpl.md` into the workspace `AGENTS.md`: read `.tackle/profile.md` / `~/.tackle/user-profile.md` and the repo's `docs/seeds/` at session start; profiles written only via `/tackle-retro`.
3. **Note the lint changes** — row 1 now exempts fenced code blocks; row 2 accepts board.md-only id lists for old formats. No workspace edit needed; the new rows apply at the next lint run.
4. **Bump the stamp** — record a `D-xx` in `decisions.md`, append a `log.md` entry, and bump the workspace `Methodology:` stamp to Tackle 3.4.x.

## v3.2 → v3.3 checklist

Run these when migrating a plan created with Tackle 3.2.x:

1. **Add §Model map + messaging capability** — copy the §Model map section from `AGENTS.tmpl.md` into the workspace `AGENTS.md` and fill in the concrete models the harness offers per tier; add the `agent-messaging: supported | unsupported` capability row to the harness map.
2. **Adopt closure reports + coordinator** (executing Full-gate plans) — every point closes with `reports/P-0N-report.md` carrying the Coordinator sign-off section (human-signed for Solo L2 points; no sign-off, no 🟢 flip); add `coordinator.md` as the Coordinator continuity projection — a projection, never canonical.
3. **Bump the stamp** — record a `D-xx` in `decisions.md`, append a `log.md` entry, and bump the workspace `Methodology:` stamp to Tackle 3.3.0.

## v3.0 → v3.1 checklist

Run these when migrating a plan created with Tackle 3.0.x:

1. **Adopt the INTENT gate** — every point briefing with remaining work gains the gate: before any behavior-changing edit the Driver writes `INTENT: current code does <X>; done-signal expects <Y>; <source> says <Z>` and stops on contradiction; add the same rule to the team protocol (`team.md` Driver duties) and to `AGENTS.md`.
2. **Adopt the 3-cycle retry bound** — point briefings and the team protocol cap self-correction at 3 failed fix-verify cycles on the same issue; after that the Driver stops, reports the actual output and current hypothesis, and escalates.
3. **Adopt two-halves verification** — every point's acceptance names both halves: the target criterion (done-signal) and surrounding-system health (regression sweep); the target passing alone is not done.
4. **Apply the triviality gate** — new work is sized against the triviality gate (one file, <10 lines, no new behavior, no searching); a task that passes it executes directly instead of earning a workspace.
5. **Note judge/eval awareness** — record in `AGENTS.md` that finished work is subject to adversarial post-completion verification (`/tackle-judge`); evidence blocks must be re-runnable because the judge re-runs claims.
6. **Record migration** — write a `D-xx` in `decisions.md`, append a `log.md` entry, and bump the workspace `Methodology:` stamp to Tackle 3.1.0.

## Artifact renames

Run these when the workspace still carries pre-3.0 artifact names (typical for plans created before Tackle 3.0):

1. **Rename the artifacts** — `contract.md` → `design-contract.md`, `strategy.md` → `execution-strategy.md`, `snapshots/` → `reference-docs/`.
2. **Update every reference** — grep the whole workspace (plan.md, point files, board.md, log.md, decisions.md, AGENTS.md, team.md) for each old name and rewrite every hit; a rename is not done while any reference to the old name remains.
3. **Handle historical-only files** — files with no current counterpart (`context.md`, `reference.md`) either map to the current artifact they belong to, or are kept as-is with a recorded `D-xx` marking them historical (never silently deleted).
4. **Record the renames** — list every rename performed in a `D-xx` in `decisions.md`.

## Structural conformance

Run these on every migrated plan — old structures fail lint rows 2 and 5 otherwise:

1. **plan.md lists every point id** — if `plan.md` §5 has no point table (2.0-era plans), add a table or list naming every `P-xx` id with its Traces-to and briefing path.
2. **Remove per-point Status fields** — delete every `**Status**:` field inside point files; `board.md` is the ONLY status source. Move any status the field carried into `board.md` first.
3. **Board status vocabulary** — board statuses use 🔴🟡⏸🟢⚪ only (⚪ = skipped/won't-do, board-only, with a one-line reason); map a deliberate skip to ⚪, never to 🟢 — a skip is not done work.
4. **Traces-to wiring** — every point file carries a `Traces to:` line; on 2.0-era formats with no "Status & wiring" block, place it in the header directly under the title.

## Citations

Run this on every migrated plan; it extends the anchoring rule (v2.1 → v3.0 item 1) with the git-historical form for targets that moved:

1. **Anchor or convert to git-historical** — every `file:line` citation is either (a) anchored and drift-checked as `path:NN — "literal fragment"` (re-verify with `/tackle-ground`), or (b) converted to the git-historical form when the target moved or drifted beyond re-anchoring: `git show <ref>:path`, noted inline — re-anchoring against the wrong content is worse than a historical-but-verifiable citation. Bare `file lines X–Y` citations must not remain.

## v2.1 → v3.0 checklist

Run these when migrating a plan created with Tackle 2.1.x:

1. **Anchor citations** — rewrite every `file:line` citation to the anchored format `path:NN — "literal fragment"`; run `/tackle-ground` and fix drift.
2. **Adopt Evidence blocks** — every "done-signal passed" claim in `log.md` must carry an Evidence block (command, trimmed output, exit line); add attempt-journal lines for failed attempts.
3. **Seal ready points** — append `SEALED: D-xx` to the Acceptance heading of each ready point and to each `design-contract.md` section that has stabilized.
4. **Run lint-spec** — execute every row of `guides/lint-spec.md` and fix failures until the score line reads `lint: N/N checks passed`.
5. **Add Last-verified stamps** — keep `reference.md` current with `Last-verified:` dates and re-ground before execution if older than the workspace window.
6. **Declare autonomy level** — add `Autonomy level: L2 (assisted)` to `AGENTS.md` (or L1/L3 with the required conditions); cap production-path points at L2 unless waived by a `D-xx`.
7. **Adopt execution rules** — apply regression sweep + maker/checker: the Driver's done-signal run is informative, the 🟢-flipping run comes from an independent checker with evidence in `log.md`.
8. **Fill the harness map** — record the concrete harness tools for read, search, test, lint, spawn, and git in `AGENTS.md`.
9. **Record migration** — write a `D-xx` in `decisions.md`, append a `log.md` entry, and bump the workspace `Methodology:` stamp to Tackle 3.0.

## v2.0 → v2.1.0 checklist

Run these when migrating a plan created with Tackle 2.0:

1. **Status migration** — if `plan.md` §5 has a Status column, move every status to `board.md` and remove the column from `plan.md`.
2. **Source anchor** — add the "Traces to" column to `plan.md` §5 and fill it for every point; add `Traces to` in each point file under Status & wiring.
3. **Grounding audit** — for each point, read every cited `file:line`; mark the point **ungrounded** if any citation is unread and update its Context.
4. **Done-signal audit** — rewrite any prose, `test -f`, or "document exists" done-signal into a literal runnable command with an explicit pass condition.
5. **Right-size** — if the plan has ≤4 points and no multi-track uncertainty, offer to collapse to `lite-plan.tmpl.md`.
6. **Spec anchors** — if `spec.md` or `constitution.md` exist, add an "Anchors" section with `A-NN` references for each traced requirement.
7. **Agnosticism sweep** — remove any harness/LLM-specific language (model brand names, vendor commands, tool-specific paths) unless the point is explicitly about that harness.
8. **Verify** — run `/tackle-verify` on the migrated plan; fix HIGH findings, decide on MEDIUM findings, note LOW findings.
9. **Record** — write a `D-xx` in `decisions.md` describing the migration, append a `log.md` entry, and bump the plan stamp/version.
