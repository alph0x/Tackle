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

## v5.4 → v5.5 checklist

Run these when migrating a plan created with Tackle 5.4.x:

1. **Check `log.md` size against the archive threshold** — lint row 13 flags `log.md` over 400 lines (workspace-overridable via `Log archive threshold: N` in the workspace `AGENTS.md`). If flagged, run the archive protocol (`status-list-next.md` §Archive): move entries older than the last 5 sessions verbatim to `log-archive.md`, append ascending, never edit moved entries, confirm the newest entry still carries its State snapshot, and record a one-line `log.md` entry. Row 6 now covers the archive pair's ordering.
2. **Ground stamps are now ISO-with-time** — `Last-verified:` is `YYYY-MM-DDTHH:MM:SSZ` (UTC); legacy date-only stamps still parse (start-of-day, conservative) and self-heal on the next ground entry. No edit needed; `tackle-check probe <workspace>` reports staleness either way.
3. **Record** — write a `D-xx` in `decisions.md` noting the version adopted, append a `log.md` entry, and bump the plan stamp.

## v5.3 → v5.4 checklist

Run these when migrating a plan created with Tackle 5.3.x:

1. **Note `tackle-check sweep`** — the release sweep now composes into one command: self-lint gates 1–7 + `catalog` + lint over every workspace (active workspaces gate the exit code; closed ones report non-gating `WARN`). Informational — no workspace edit.
2. **Record** — write a `D-xx` in `decisions.md` noting the version adopted, append a `log.md` entry, and bump the plan stamp.

## v5.2 → v5.3 checklist

Run these when migrating a plan created with Tackle 5.2.x:

1. **Note the two-phase drift check** — `ground.md` step 2 is now two-phase: the line
   check first; on failure, a whole-file fallback counts matches — exactly one ⇒ the
   citation is **re-anchored** mechanically (`path:NN` → `path:MM`, literal rewrite, zero
   model judgment); zero ⇒ stale (unchanged behavior); more than one ⇒ ambiguous, flagged
   with the match count. Staleness is decided by content, never session memory.
2. **Note `tackle-check ground <workspace>`** — the runner's first writing gate: scans
   `plan.md`/`reference.md`/`points/*.md`, re-anchors drifted citations in place (staged,
   `cmp -s`-gated), prints one line per citation, exit 0 iff zero stale and zero
   ambiguous. Lint row 4 stays read-only and names it as the fix path. Existing
   citations with line-accurate fragments are untouched.
3. **Raise fragment uniqueness** — new point briefings should pick a fragment appearing
   on exactly one line of its file (the re-anchor needs a unique match); existing
   fragments keep grounding on their cited line (phase 1), only their re-anchorability
   changes.
4. **Note the executor-contract wording** — `AGENTS.tmpl.md` item 4: on drift, re-anchor
   mechanically per the two-phase rule before hand-editing anything.
5. **Run the sweep once** — `sh tackle-check lint <workspace>`; then `sh tackle-check
   ground <workspace>` if any citation is stale.
6. **Record** — write a `D-xx` in `decisions.md` noting the version adopted, append a
   `log.md` entry, and bump the plan stamp.

## v5.1 → v5.2 checklist

Run these when migrating a plan created with Tackle 5.1.x:

1. **Add the usage ledger** — copy `references/usage.tmpl.md` into the workspace as
   `usage.md`; from now on every role run (point roles, planning sessions, retro) appends
   one row per the template's schema (Point/Role/Tier/Model/Effort/Tokens in/Tokens
   out/Session; column meanings are documented in the template's header prose).
   Historical rows are never backfilled — the ledger starts at adoption.
2. **Add the capability lines + effort map** — the workspace `AGENTS.md` §Harness map gains
   the `usage-reporting: supported | partial | unsupported` row; §Model map gains the
   effort table (`low / medium / high / max` bound to the harness's concrete settings) and
   the `effort-binding: supported | unsupported` line under `model-binding`. `partial` =
   cumulative total only (record it in Tokens in, `n/a` out); `unsupported` = `n/a` token
   fields, rows still appended; recording is informative, never gating.
3. **Note the Effort field + role defaults** — point briefings may declare
   `**Effort**: inherit | low | medium | high | max` (overriding the `team.tmpl.md` role
   defaults). Binds at the next point execution — existing briefings need no rewrite.
4. **Note lint rows 11–12** — the runner now enforces usage rows for done points (row 11;
   guard-skips until `usage.md` exists — item 1 creates it) and the effort vocabulary
   (row 12). Run `sh tackle-check lint <workspace>` once after item 1.
5. **Note the runner parser change** — `tackle-check done-signal` now extracts both
   `**Run**:` and `**Done-signal**:` labels and FAILS on empty extraction (no silent
   green); review-gate briefings are unaffected.
6. **Record** — write a `D-xx` in `decisions.md` noting the version adopted, append a
   `log.md` entry, and bump the plan stamp.

## v5.0 → v5.1 checklist

Run these when migrating a plan created with Tackle 5.0.x:

1. **Note the removed companion check** — intake Step 0 no longer checks for, recommends, or installs external planning skills; planning is self-contained (intake, simplicity, and architecture guidance live in `references/guides/` and the templates). Informational — no workspace edit.
2. **Note the intent-exploration essentials** — the adopted intent-exploration discipline (explore intent before solutions; infer first, then ask; batch questions with defaults) now lives in intake Step 1 of `intake-and-gate.md`. Informational — no workspace edit.
3. **Note the simplicity ladder** — `team.tmpl.md` now defines the ladder the Simplicity Auditor runs (does it need to exist → reuse in-codebase → stdlib → native → installed dependency → one line → minimum code) and the security checklist the Security Reviewer runs; workspaces with an instantiated `team.md` may copy the blocks, new workspaces inherit them. Optional adopt.
4. **Note the architecture guidance** — Step 5.5 of `design-and-contract.md` now carries the architecture-decision checklist (dependency rule, SOLID checks, foundations grounding) with a pointer from `foundations.tmpl.md`. Informational — no workspace edit.
5. **Note the Output-contract carve-out** — the `SKILL.md` Output contract gains the Auto-Clarity carve-out: terse by default, but say it fully for security warnings, irreversible actions, or anywhere compression risks misread. Informational — no workspace edit.
6. **Record** — write a `D-xx` in `decisions.md` noting the version adopted, append a `log.md` entry, and bump the plan stamp.

## v4.4 → v5.0 checklist

Run these when migrating a plan created with Tackle 4.4.x:

1. **Adopt the double gate (5.0)** — the flip now requires `tackle-check done-signal <point>` green AND the independent checker's sign-off (workspace flag `tackle-check-gate: on|off`, default on for new workspaces). Decide the flag: **on** = mechanical gate + sign-off; **off** = 4.x flip semantics preserved. The runner ships with the install artifact (`SKILL.md` + `references/` + `tackle-check`); run `sh tackle-check lint <workspace>` once to confirm the workspace lints clean before flipping anything.
2. **D-02 revoked** — `guides/lint-spec.md` no longer forbids shipped scripts; the runner composes the lint rows (the runner IS the rows, the table is its spec). Existing hand-run lint flows still work verbatim.
3. **Record** — write a `D-xx` in `decisions.md` noting the version adopted + the `tackle-check-gate` decision, append a `log.md` entry, and bump the plan stamp.

## v4.3 → v4.4 checklist

Run these when migrating a plan created with Tackle 4.3.x:

1. **Note the slimmed entry navigation** — the `SKILL.md` routing table keeps one canonical trigger per mode (the "(any language)" header covers phrasing) and the execution-loop rules are compressed to one-liners with pointers to `team.tmpl.md` / `AGENTS.tmpl.md` §Autonomy; the "Commands are entry points" note moved to `guides/intake-and-gate.md`. Command surface, status vocabulary, artifacts, and closure protocol are unchanged. Informational — no workspace edit.
2. **Record** — write a `D-xx` in `decisions.md` noting the version adopted, append a `log.md` entry, and bump the plan stamp.

## v4.2 → v4.3 checklist

Run these when migrating a plan created with Tackle 4.2.x:

1. **Adopt the test-first default** — `plan.md` §6.1 now expects test-first for code points (red phase seen failing before implementation; opting out requires a `D-xx`). Doctrine and depth tiers (unit / acceptance / property / fuzz-torture / mutation) live in `guides/testing.md`. Existing plans keep running; new or revised points follow the default.
2. **Note the Test depth axis** — `guides/quality-dimensions.md` gains a Test depth row: fired tiers fold into point done-signals as runnable fragments. Informational for in-flight points — no rewrite required.
3. **Record** — write a `D-xx` in `decisions.md` noting the version adopted, append a `log.md` entry, and bump the plan stamp.

## v4.1 → v4.2 checklist

Run these when migrating a plan created with Tackle 4.1.x:

1. **Note grade derivation in `SKILL.md`** — the closure-report bullet now states the recorded grade is derived from the section-4 evidence block (checker command + output + exit line), never from a declared grade; `board.md` legends already carry the rule. Informational — no workspace edit.
2. **Record** — write a `D-xx` in `decisions.md` noting the version adopted, append a `log.md` entry, and bump the plan stamp.

## v4.0 → v4.1 checklist

Run these when migrating a plan created with Tackle 4.0.x:

1. **Note skill self-update** — the installed skill now checks for a new release daily during planning intake (Step 0 "Self-update check") and self-updates via `guides/update.md`; `/tackle-update` forces it. Informational — no workspace edit.
2. **Note the standard lens catalog** — `team.tmpl.md` §Opt-in `Lenses:` gained six standard lenses (`correctness`, `security`, `repro`, `performance`, `simplicity`, `polish`) with declaration triggers. `Lenses:` stays opt-in; old briefings need no rewrite. Informational — no workspace edit.
3. **Record** — write a `D-xx` in `decisions.md` noting the version adopted, append a `log.md` entry, and bump the plan stamp.

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
