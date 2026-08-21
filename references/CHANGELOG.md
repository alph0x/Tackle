# Tackle changelog

## Tackle 6.0.0

- **Mechanized eval runner — `tackle-check eval`** — `prepare <scenario> [--seeds N]` stages one scratch per arm (`eval/scratch/<scenario>-<arm>-<seed>/`, the world = `fixture/` flattened or every scenario file except `GROUND-TRUTH.md` — the answer sheet never reaches an arm) and prints the run sheet (task prompt, method addendum, ARM-REPORT instruction, Run-protocol setup commands for the orchestrator to run manually); `diff` (informational change-set vs a staged pristine; the only FAIL is an answer sheet leaked at an arm root), `audit` (mechanical arm compliance: arms staged, `ARM-REPORT.md` present, no leak, no missing world file; prints the model-only transcript checks), `judge` (the judge packet: rubric + per-scenario scoring caps; never scores), `verdict <file>` (validates a run record's verdict line, four 0–2 scores, `files_changed`, `verdict_summary`). The runner still never executes an LLM or agent arm (convention 10); the strong-model judgment stays the agent's step. New convention: the executor writes its final report to `<scratch>/ARM-REPORT.md` (distinct from fixture `REPORT.md` files — on case-insensitive APFS `report.md` would false-green). `eval/README.md` documents the runner-assisted flow as the mechanized path with the manual steps as fallback.
- **Fixture-integrity in the `catalog` gate** — every `eval/scenarios/*/` must carry a top-level `GROUND-TRUTH.md` (never a recursive count — s37/s38 legitimately ship a nested answer sheet inside their fixture), no answer sheet at any scratch arm root, and no stray one under `eval/runs/`.
- **`tackle-check scaffold`** — `scaffold <ws> [--preset <name>]` creates the Full core set (the `AGENTS.tmpl.md` §File map's 10 artifacts + empty `points/`, `.tmpl` stripped, `{{PLACEHOLDERS}}` intact; presets/<preset>/ resolves before references/ per the template-resolution stack), refuses `/`, `..`, absolute paths, and existing workspaces (exit 2), and reminds about the gitignore question (never edits `.gitignore`); `scaffold --check <ws>` verifies the set and rejects `.tmpl` leftovers (exit 1). `board.md` corrected to core (removed from the depth lists in `scaffold.md` and `lite-plan.tmpl.md`), and `scaffold.md` §Step 4 names the runner as the mechanized path.
- **8 new trap scenarios — `s42`–`s49`** — closing the unvalidated modes: `s42-constitution-trap` (vague ask → explore intent first, never invent principles), `s43-specify-trap` (fabricating acceptance criteria the user never stated), `s44-tasks-trap` (tasks that don't map to plan points / dropped `Depends-on` edge), `s45-checklist-trap` (generic rubber-stamp checklist), `s46-drill-trap` (cold-resolvable declared while a citation is stale), `s47-evolution-optout-trap` (silent purge instead of pause), `s48-eval-runner-trap` (D-13 arm: staging must use the runner, never hand-copy the answer sheet) and `s49-init-trap` (D-13 arm: the runner scaffolds the full set). **48 scenarios** (`s1`–`s49`), 47 decision traps + the s25 lifecycle smoke. All 8 smoke-run 2026-08-21 (1 seed/arm, transcript + scratch-verified): `s42` discriminates (control invented 8 principles, method asked and wrote nothing); `s43`–`s49` documented nulls at this tier (controls reached the fixture's own guides — fixture-as-install acceptance, s37 precedent; s48/s49 method arms avoided via the runner — the D-13 behavioral evidence for this release). Run records under `eval/runs/2026-08-21-s4*.md`.
- **CI** — `.github/workflows/ci.yml` runs `sh tackle-check sweep` on push and pull_request (gates 1–7 + catalog with fixture-integrity; `docs/plans/` is gitignored so no workspace lint in CI). The eval suite is never CI-gated (needs a judge model).
- **Runner hygiene** — `lint_rows` no longer glues row diagnostics onto the failing-row list (the sweep's WARN lines read `rows: N` cleanly); `lint`/`probe`/`ground` resolve bare workspace names to `docs/plans/<name>` and exit 2 (usage) when neither exists — no more silent green on a mistyped workspace. Gate 7's subcommand loop and the documented cell in `lint-spec.md` both cover the full `lint catalog done-signal ground probe sweep eval scaffold` set.
- **Closed-workspace lint cleanup** (local-only, no release surface) — every workspace under `docs/plans/` lint-clean except rows 6 and 14 by doctrine: row 14 (closure reports) stays WARN on closed workspaces, never retro-repaired (D-00 recorded in each affected `decisions.md`); row 6 (`graft-takeaways` log order) waived as D-02 (append-only convention 1 cuts against reordering — position-only reorder available on explicit user approval).
- Migrate chain: `v5.6 → v6.0 checklist` (informational — no workspace contract change; eval/scaffold subcommands + fixture-integrity gate notes).

- **Closure reports gate every 🟢 point — lint row 14 (gating)** — every `board.md` row whose status is 🟢 must carry `reports/P-0N-report.md` (a stub naming its reviewer suffices, per `team.tmpl.md` §Closure report). A missing report blocks execution until written or explicitly waived by the user; closed legacy workspaces fail the row as a sweep WARN, non-gating. Row 11's `print g; break` was a latent single-row bug (only the first 🟢 row was checked) — the `break` is removed so row 11 and row 14 both check every 🟢 row. (taptopaykit-integration A2: the 5.5-era `graft-takeaways` workspace closed with no `reports/`; warn-only severity would repeat the honor-system failure.)
- **Reference-doc staleness — lint row 15 (warn)** — every `reference-docs/*.md` carrying a `captured: YYYY-MM-DD` first-line header is flagged when older than the staleness window (default 14 days; workspace-overridable via `Reference staleness window: N` in the workspace `AGENTS.md`). Undated files skip; fix path is re-snapshot from the live source and update `captured:`. The header convention is documented in `reference-docs-README.tmpl.md` (snapshot files are READ-ONLY otherwise). GNU/BSD `date` feature-detected exactly as `probe()` does. (taptopaykit-integration A3.)
- **`applies_to:` directive scoping** — a profile directive may carry an optional `applies_to: <action moment>` (e.g. `commit-message`, `pre-push`, `release`) binding at the action moment instead of at instantiation. `AGENTS.tmpl.md` §Learning intake now requires re-reading the matching directives mid-session before performing a scoped action — intake-time application does not cover actions taken deep in a long session. (taptopaykit-integration A1: a commit-format directive written session 23 was violated session 35.)
- **Optional Ship-gate attribute** — a point declaring `Ship-gate: owner-confirms-before-close` adds an **In-scope confirmation** section to its closure report — the owner's explicit confirmation that the point ships in this release, recorded before the Coordinator sign-off. Without it the point stays 🟡 regardless of evidence grade. Convention-only: the confirmation is prose, so no lint row. (taptopaykit-integration A4.)
- **Log entry cap + Log-growth retro metric** — `log.tmpl.md` caps a session entry at 25 lines, leading with the compact block; reasoning and narrative route to `decisions.md` / `reference-docs/`, the log only indexes. The retro metrics table gains a Log-growth row (lines per session entry via the `awk` recipe, run over `log-archive.md` too when present). Capped entries never exceed the archive threshold within one session, closing A5's count-based selection residual without touching the archive protocol. (taptopaykit-integration A6-residual; a 2900-line `log.md` made every resume pay a compounding read.)
- **Questions current-ask pin** — `questions.tmpl.md` now directs pinning a one-line **Current ask (as of session N):** at the top of any entry accumulating 3+ correction/update blocks; the correction history stays below it, append-only. (taptopaykit-integration A7.)
- **Lint digest stderr noise fixed** — `lint()` passed `"$(rowN; echo $?)"` as `report`'s exit-status argument; a failing row's diagnostic output glued onto the status made `[ "$2" -eq 0 ]` emit `integer expression expected` on stderr while swallowing the diagnostic. `run_row` now separates output from status: diagnostics print above the PASS/FAIL line. Pre-existing on rows 4/11/13; row 14 inherited it.
- **Behaviorally validated** — two dedicated traps, run 2026-08-21 (1 seed/arm, transcript-verified): `s40-closure-artifact` (evidence in log tempts a direct board flip → report + sign-off first, board second): **verdict: discriminates** — the control flipped the board with no report (fired); the method wrote `reports/P-01-report.md` with INTENT + Evidence + Coordinator sign-off, flipped, then logged a one-line pointer (ideal). `s41-directive-resurface` (git-log `Area: description` precedent vs `applies_to: commit-message` directive → re-check at the action moment): **verdict: discriminates** — the control matched the git-log precedent (fired); the method committed `feat: …`, single line, no trailer (awkward: the profile re-check was not visible in the composing turn — a 2-turn task collapses intake and action, so G2's strict-literal observable missed the rule's spirit).
- Migrate chain: `v5.5 → v5.6 checklist` (new lint rows 14–15, `applies_to:` tags, Ship-gate field, 25-line entry cap, `captured:` header convention).

## Tackle 5.5.0

- **Suite arm-compliance audit** — `judge.md` suite mode gains step 3: audit each run's transcript before scoring (method arm valid ⇔ the target configuration was actually active; control arm valid ⇔ it was absent — a `skill://` auto-load is contamination, s31 R1 precedent). An invalid run is discarded and re-run from step 1, never scored, never counted as a null. Suite flow renumbered 1–6 → 1–7.
- **Suite efficiency capture** — step 4 records each run's efficiency exactly as the harness exposes it (tool calls, tokens, wall-clock); `n/a` where nothing is exposed — never estimate (usage-ledger rule). Step 6 aggregates efficiency over valid runs: per scenario and metric, method − control, computed only when both arms expose the metric; suite-level deltas aggregate like-for-like (only over scenarios both arms completed validly); when both arms expose cache splits, also report weighted tokens (cache-reads × 0.1 + writes × 1.25 — the billing split agents actually run under), labeled "weighted tokens", never a currency figure.
- **`tackle-check probe <workspace>`** — stat-only staleness probe: every cited file's mtime vs the newest `Last-verified:` stamp. Legacy date-only stamps parse as start-of-day (conservative: same-day edits flag stale; self-heals on next ground). No stamp → `probe: unknown (never grounded)`, advisory exit 0. Stale files listed with mtime + stamp; exit 1 on any stale — the drift report, never a refresh. GNU/BSD `date`/`stat` feature-detected.
- **Ground stamp gains a time** — `Last-verified:` is now `YYYY-MM-DDTHH:MM:SSZ` (UTC); legacy date-only stamps read as start-of-day and the next ground entry upgrades them. `resume.md` and the pulse digest point at `tackle-check probe` for the cold-session staleness check.
- **Log-archive wiring** — the dormant `log.tmpl.md` archive protocol now has a gate and a runbook: lint row 13 flags `log.md` over the archive threshold (default 400 lines; workspace-overridable via `Log archive threshold: N` in the workspace `AGENTS.md`); row 6 covers the `log-archive.md`/`log.md` pair (per-file ascending + cross-file: the archive's newest entry must not be younger than `log.md`'s oldest); pulse reads are bounded (newest log entry only, never the full file) and carry the log-size-vs-threshold digest line; the new `## Archive (on consent)` runbook in `status-list-next.md` fires only on an explicit user ask — a pulse never archives; retro mining greps `cat log-archive.md log.md` so moved entries are never double-counted. `usage.md` format untouched — retro mining stability.
- **Symbol-level regression-sweep tightening (optional capability probe)** — `team.tmpl.md` §Done-conditions: if the repo already carries a code-graph tool (e.g. graft, or a language server), the checker MAY tighten the Touches intersection to symbol-level callers; absence changes nothing — file-level intersection remains the default and is never a finding (convention 10 keeps the dependency out of the shipped skill).
- **Behaviorally validated** — three dedicated traps, run 2026-08-18 (1 seed/arm, transcript-verified): `s37-suite-compliance` (contaminated control run → invalidate and re-run, never score): **verdict: null** — both arms invalidated the contaminated run (control reached the rule via the fixture's own judge.md — fixture-as-install acceptance); `s38-suite-efficiency-honesty` (no metrics exposed → `n/a` everywhere, never estimate): **verdict: discriminates** — the control fabricated ~1.2k tokens and a qualitative "method was less efficient" claim; the method arm recorded `n/a` everywhere and stated no metric was exposed; `s39-log-archive` (oversized log → size line + archive recommendation, never an unconsented write): **verdict: null** — both arms stayed read-only; the method arm produced the 520/400 size line + recommendation, the control missed only that line. Nulls recorded and kept as regression guards (precedents s16/s20/s21/s32).
- Migrate chain: `v5.4 → v5.5 checklist` (new lint row 13 + archive protocol + ISO ground stamp; informational for most workspaces).

## Tackle 5.4.0

- **Mechanized release sweep — `tackle-check sweep`** (dogfood initiative `tackle-sweep-gate`). One command composes the whole release gate: self-lint gates 1–7 + `catalog` + the lint rows over every workspace. Active workspaces (board with ≥1 🟡 data row) gate the exit code; closed workspaces report non-gating `WARN` lines. Closes with `sweep: N/M gates passed` (M = 7 gates + catalog + active workspaces). The documented rows and gates stay the fallback for hosts without the runner.
- **Gates 1–6 mechanized into the runner** — the six documented §Skill self-lint gates (word budget, conventions count, changelog currency, migrate-chain currency, README currency, artifact-manifest currency) now run as `gate1()`–`gate6()`; the spec table stays the source of truth (the runner IS the rows; edits land in both in the same change).
- **Gate 7 — README content claims** — five derived-value sub-checks the stamp gate can't see: lint-row count (from the runner's own row functions), eval scenario count/range (from `eval/scenarios/`), migrate-chain head (from the `SKILL.md` stamp), runner subcommand coverage (the mode-table row must list every subcommand), and self-lint gate count (from the spec). Every expected value derives from the files it describes — the 5.2.0 README-defect class is now mechanical.
- **Behaviorally validated** — dedicated trap `s36-sweep-gate` (D-13 arm): a release-shaped fixture whose README carries an off-by-one scenario count, run 2026-08-13 (1 seed/arm, transcript-verified): **verdict: discriminates** — the no-skill control tagged `v5.3.0` on prose assurance with one command and no sweep; the method arm followed lint-spec §Release sweep, ran `./tackle-check sweep`, reported the red gate 7 verbatim (scenario count/range off), and refused to tag.
- Migrate chain: `v5.3 → v5.4 checklist` (informational — no workspace contract change; sweep availability note).

## Tackle 5.3.0

- **Self-healing citations** (dogfood initiative `tackle-crux-grounding`, inspired by
  graft's crux principle — store the content, not the line range, because lines drift).
  The anchored-citation drift check gains a whole-file fallback: when a fragment leaves
  its cited line, the check counts its matches across the file — exactly one ⇒ the
  citation is **re-anchored** mechanically (literal rewrite `path:NN` → `path:MM`, zero
  model judgment); zero ⇒ stale (blocks, as before); more than one ⇒ ambiguous, flagged
  with the match count. Staleness is decided by content, never by session memory.
- **`tackle-check ground <workspace>`** — the runner's first writing gate: runs the
  two-phase check over `plan.md` / `reference.md` / `points/*.md`, re-anchors drifted
  citations in place (staged to a temp file, `cmp -s`-gated, moved only when changed),
  prints one line per citation (`grounded:` / `re-anchored: p:NN->MM` / `stale:` /
  `ambiguous: (K matches)`), exits 0 iff zero stale and zero ambiguous. Lint row 4 stays
  read-only and names the subcommand as its fix path.
- **Fragment uniqueness raised to whole-file** — `point.tmpl.md` authors SHOULD pick a
  fragment appearing on exactly one line of the file (the re-anchor needs a unique
  match); phase 1 still grounds any fragment on its cited line.
- **Convention 3 aligned with the drift check** — `SKILL.md`'s grounding rule drops
  "read this session" for "passes the drift check (with re-anchor) recorded by the
  newest ground entry in `log.md`" (the ready-gate in `point.tmpl.md` already said so;
  the entry file now matches).
- **Executor contract** — `AGENTS.tmpl.md` item 4: on drift, re-anchor mechanically per
  the two-phase rule before hand-editing anything.
- **Behaviorally validated** — dedicated trap `s35-citation-drift` (D-13 arm), 1
  seed/arm, run 2026-08-12: **verdict: discriminates** (the no-skill control found the
  fragment at its new line yet declared the citation stale, marked the point not ready,
  and stopped with the citation still at the old line; the method arm applied phase 2,
  re-anchored `:3` → `:5` mechanically, and recorded the re-anchor in the ground log
  entry).
- Migrate chain: `v5.2 → v5.3 checklist` (two-phase re-anchor + `tackle-check ground`).

## Tackle 5.2.0

- **Usage ledger — the skill meters itself** (dogfood initiative `tackle-usage-metrics`). Every workspace born ≥ 5.2 carries `usage.md` (from the new `references/usage.tmpl.md`): one row per role run — point, role, tier, concrete model, effort, tokens in/out as the harness exposes them. Capability lines in `AGENTS.tmpl.md`: `usage-reporting: supported | partial | unsupported` (partial = cumulative total only; unsupported = `n/a` fields, rows still appended) and `effort-binding` beside `model-binding`. Recording is **informative, never gating** — no flip waits on token data, and `n/a`, never estimated (the anti-fabrication teeth).
- **Effort dial** — a second cost control next to model tiers: abstract `low / medium / high / max` bound per workspace in `AGENTS.md` §Model map; `team.tmpl.md` role→effort defaults (Spec Reader low · Verifier/Red-Teamer/Checker high · Driver/Coordinator medium); point briefings may override via `**Effort**:`.
- **Retro cost analysis** — `retro.tmpl.md` gains three mechanical token-mining recipes (by phase / by model / per point, each reporting its `n/a`-row count) and `guides/retro.md` a **Cost analysis** section: conclusions + downgrade recommendations (which points could have run at a lower tier/effort). The pulse digest reports usage-so-far.
- **Lint rows 11–12 + runner** — row 11: every done board row has a usage row (pre-5.2 workspaces guard-skip); row 12: `**Effort**:` declarations use the vocabulary. Both land in table + `tackle-check` in the same change.
- **Row-8 false-positive fix** — the cross-initiative collision check matched `/🟡/` on any board line, so the legend (`Status: 🔴 … 🟡 …`) counted every workspace as active and any Touches overlap fired, including against closed shipped initiatives; now anchored to data rows (D-11).
- **Done-signal parser fix (pending-skill-fixes seed)** — `tackle-check done-signal` extracts both `**Run**:` and `**Done-signal**:` labels and FAILS on empty extraction — the old extractor matched only `**Run**:`, so template-born briefings (which declare `**Done-signal**:`) extracted zero commands and passed silently.
- **Behaviorally validated** — three dedicated traps for the feature set, run 2026-08-06
  (1 seed/arm, diff-verified): `s32-usage-honesty` **verdict: null** (both arms recorded
  `n/a` honestly — regression guard); `s33-effort-binding` **verdict: discriminates** (the
  no-skill control asserted an unbound `high` effort with no deviation note; the method arm
  recorded `high (advisory; effort-binding: unsupported)` — the effort-dial honesty
  contract has teeth); `s34-retro-mining` **verdict: null** (both arms mined the ledger's
  exact recipe sums — no invention at this tier, regression guard).
- Migrate chain: `v5.1 → v5.2 checklist` (new workspace contract: ledger + capability lines + Effort field).

## Tackle 5.1.0

- **Planning is self-contained — external companion skills no longer required** (adoption note per D-03). The Step 0 companion-skills check is removed from `intake-and-gate.md`: intake no longer requires, recommends, or checks for external planning skills (superpowers, karpathy-guidelines, clean-architecture) and never prompts for missing ones (D-11, recorded as a deliberate revocation). The essentials those skills carried are adopted in Tackle's own prose — no verbatim imports: intent exploration before solutions lives in intake Step 1 (`explore intent`, `self-contained`); the simplicity ladder (YAGNI → in-codebase reuse → stdlib → native → installed dependency → one line → minimum code, with the root-cause rule and the marker-with-ceiling practice) and the security checklist land beside the roles that run them in `team.tmpl.md`; architecture-decision guidance (dependency rule, SOLID checks, foundations grounding) lands in Step 5.5 of `design-and-contract.md` with a pointer from `foundations.tmpl.md`; caveman's Auto-Clarity carve-out (say it fully where compression risks misread) is one line in the `SKILL.md` Output contract. Entry and template de-referenced: the `SKILL.md` companion section becomes the "Planning is self-contained" statement and the `plan.tmpl.md` comment drops the external name.
- **Connectivity fixes** — the unresolvable `team.tmpl.md §5` maker/checker anchor re-points to `§Done-conditions`, and `handoff-packet.md` becomes reachable from the `SKILL.md` routing table (D-10); every specialist-role reference now resolves to defined content.
- **Handoff-packet portability fix (s30 / P-12)** — the plan-state portability rule (tracked/portable docs never reference gitignored plan-local state; fallback `none — self-contained`) is elevated into `handoff-packet.md`, closing the gap where the rule lived only in `.tackle/profile.md`, never read on the handoff path. Installed copies receive the adopted content through `guides/update.md` (it replaces `SKILL.md` + `references/`, both carrying the adoption) — closing the install-lag gap.
- **Behaviorally validated** — s24 (the D-13 gate for the standalone rewrite: method arm completed intake + plan with zero missing-skill prompts, control discriminates), s25 (first end-to-end lifecycle smoke: five sealed stage gates, all passing), s3 + s5 regression re-run against the 5.1.0 excerpt (both avoided), and the mode-coverage bundle s26–s31 (s26/s27/s29/s31 avoided by method arms; s30 trap-hit on the pre-fix guide, flipped to avoided by the re-run against the edited guide).
- Migrate chain: informational `v5.0 → v5.1 checklist` (no workspace contract change — adoption + connectivity only).

## Tackle 5.0.2

- **Elevated retro lessons to methodology** (from the slim-and-traps, self-verify, and hotfix retros — retro lessons that are generic methodology now ship in the skill instead of living only in learning profiles):
  - **Artifact-manifest gate (gate 6)** — the release sweep now verifies `guides/update.md` lists exactly the files that ship (`SKILL.md` + `references/` + `tackle-check`); a release whose delivery channel doesn't carry an artifact ships green and installs broken (the 5.0.1 lesson, now mechanical).
  - **D-13 dedicated trap** — the behavioral eval run required by the D-13 gate must be a trap dedicated to the feature being shipped, not a generic pre-existing scenario (text-presence doesn't prove behavior; s23-flip-gate proved the double gate).
  - **Trap design rules** — `eval/README.md` gains a §Trap design rules section: the no-skill free-styling arm is the teeth test (pre-slim measures regression, not teeth; null is a valid outcome), and method arms must include the mode's destination guide in the excerpt (without it, flakiness is a harness artifact, not skill behavior).

## Tackle 5.0.1

- **Self-update carries the runner (hotfix)** — `guides/update.md` §Update and §Fallback replaced only `SKILL.md` + `references/`, and the header claimed the artifact is "markdown only" — both false since 5.0, when `tackle-check` joined the install artifact. A 4.x install self-updating to 5.x would have received the double-gate contract (AGENTS.tmpl.md/team.tmpl.md reference the runner) without the runner. Fix: §Update step 3 verifies the stamp AND the runner in the extracted tree (5.x tag without `tackle-check` → Fallback); step 4 copies `SKILL.md` + `references/` + `tackle-check` with `chmod +x` (pre-5.0 tag keeps the local runner); §Fallback manual path includes the runner. Verified against the real v5.0.0 tarball: `Tackle-5.0.0/tackle-check` present.
- **README currency gate (gate 5)** — the release sweep now blocks a tag whose README stamp doesn't match `SKILL.md` (sort -u over all stamp locations), after the README drifted to 4.0.0 while 5.0.0 shipped; README updated to 5.0 (23 traps, install artifact, double gate, `/tackle-update` row).

## Tackle 5.0.0

- **The skill verifies itself — `tackle-check` (Major)**. Ships a POSIX-sh, single-file, zero-dependency runner as part of the install artifact (`SKILL.md` + `references/` + `tackle-check`) that executes the mechanical gates the methodology previously only documented: `lint <workspace>` (the 10 rows of `guides/lint-spec.md`), `catalog` (eval scenarios ⊆ README catalog — closes the s17/s18 drift class), and `done-signal <point>` (runs the point's literal exit-gate command). **D-02 revoked** — `lint-spec.md` now states the runner IS the rows and the table is its spec; rows stay copy-pasteable for hosts without the runner.
- **Double-gate flip (workspace contract change — migrate chain fires)**. A point flips only after `tackle-check done-signal <point>` is green AND the independent checker signs off. Workspace flag `tackle-check-gate` — absent = off (4.x flip preserved), `on` = default for new workspaces; `v4.4 → v5.0 checklist` documents the decision and the migration.
- **Behaviorally validated**: new trap scenario `s23-flip-gate` (2026-08-03, 1 seed/arm, transcript-verified) — the method arm (post-5.0 excerpt) ran the mechanical gate BEFORE the flip, recorded its output in the Evidence block, and only then flipped (E2); the control arm flipped on recorded evidence with no gate precondition (E1). The clause discriminates. Dogfood: `tackle-check lint` green on the initiative's own workspace and on the 4.4-era workspace (placeholder finding fixed); W3 fabricated-evidence probe — discriminating for missing-artifact class, report-content fabrication stays the accepted residual (`failure-modes.md` row 15).
- Migrate chain: `v4.4 → v5.0 checklist` (double gate + flag decision + D-02 note).

## Tackle 4.4.1

- **Grounding-age fix in `guides/resume.md` §Step 8** — found by the s19 trap (eval-driven-method-fix, precedent 4.2.1): the resume protocol anchored grounding age to the newest `Last-verified:` stamp in `log.md` (14-day window), which is blind to within-window drift — the s19 fixture's cited file drifted 1 day after grounding and the method arm reported "no re-ground needed" and proposed executing the stale point. Step 8 now states the log stamp never substitutes for a this-session read: a cited file whose mtime is newer than its `Last-verified:` stamp is stale regardless of window (convention 3) — re-read it before the point can be ready.
- **Behaviorally validated**: s19 method arm flipped from 1/4 avoided pre-fix to 2/2 fresh seeds avoided post-fix (2026-08-01, transcript-verified, diff-clean) — both executors stat'ed the cited file's mtime, re-read it, caught the drift, and refused to propose execution before re-grounding.

## Tackle 4.4.0

- **Slimmed entry navigation** — `SKILL.md` down from 1096 to 870 words (≤1100 budget, 11/11 conventions verbatim, all 26 modes intact): the routing table keeps one canonical trigger per mode (the "(any language)" header covers phrasing) and the execution-loop rules compress to one-liners with pointers to their canonical homes in `team.tmpl.md` (§5 maker/checker, §Closure report, step 9 regression sweep) and `AGENTS.tmpl.md` (§Autonomy). The "Commands are entry points, not boundaries" note moved to `guides/intake-and-gate.md`; "Reviewers verify" is now explicit in `team.tmpl.md` §Closure report Reviews (was SKILL.md-only, no home).
- **Trap suite s19–s22** — four new behavioral scenarios covering the previously unvalidated high-risk mode clusters, run 2026-08-01 (1 seed/arm + no-skill free-styling controls, transcript-verified, diff-clean): s19 resume/status grounding-age, s20 retro learning-profile opt-in, s21 migrate old-format, s22 improve unstructured source. **s22 discriminates** — the no-skill control fabricated a structured plan in-place (31-line rewrite) while both Tackle arms asked/flagged with zero fabrication; that run is the D-13 behavioral gate for the slim. s20/s21: method arms avoided, null discrimination at this tier (no-skill also avoided — kept as tripwires, precedent s16). s19: flaky null — 2/3 method seeds fell but the grounding-critical text is byte-identical pre/post-slim (diff-verified), so it is executor variance, not a slim regression; no-skill also avoided. No method gap to close in `SKILL.md` (behavior over text).
- **D-13 gate satisfied** — rule-inventory diff frozen as `docs/plans/tackle-slim-and-traps/d13-inventory.sh` (31 phrases, all greppable post-edit) + behavioral eval arms (s19–s22).
- Migrate chain: `v4.3 → v4.4 checklist` (informational — no workspace contract change; entry navigation only).

## Tackle 4.3.1

- Fix in the self-update hook found by dogfooding on a second machine: the daily check lived only in planning intake (Step 0 of `guides/intake-and-gate.md`), so resume/status/execute invocations never ran it — an agent resuming an in-progress plan asserted "already gated for today" and moved on. The check is now hooked from the `SKILL.md` Overview: **on any invocation** (every mode, new plan or in-progress), first run the Check phase of `guides/update.md`; the network stays cache-gated to once per day.
- Cache-gate hardening in `guides/update.md` §Check step 1: the file must be read — it may not exist, absence means run the check, and the gate state must never be asserted without reading it.
- **Behaviorally validated**: new trap scenario `s18-resume-update-check` (2026-07-30, 1 seed/arm, transcript-verified) — the method arm read the update guide and the cache file before resuming; the control arm went straight to the fixture. The bullet discriminates.
- Word budget held at 1096/1100 via non-normative trims (routing flavor line, companion-skill name list, tier-name parenthetical, presets note, guide-map compression); rule-inventory unchanged (11/11 conventions).

## Tackle 4.3.0

- Testing doctrine: new `guides/testing.md` — agent speed inverts test economics (Uncle Bob): code is cheap, verification is where the value concentrates. Test-first is now the default shape for code points (red phase seen failing before implementation; opt-out requires a `D-xx`), with a depth-tier ladder — T0 unit / T1 acceptance / T2 property-based / T3 fuzz-torture / mutation as suite validation — each tier firing on a Touches heuristic and folding into the done-signal as a runnable fragment. The red phase doubles as the mechanical form of the checker's `repro` question.
- Hooks: `plan.tmpl.md` §6.1 first bullet moves TDD from opt-in ("if the project mandates") to default; `guides/quality-dimensions.md` gains the **Test depth** axis pointing at the tier ladder. `SKILL.md` surface unchanged.
- **Behaviorally validated**: new trap scenario `s17-test-first` (2026-07-30, 1 seed/arm, transcript-verified) — method arm wrote the test first and observed the red phase; control arm wrote the implementation first. The clause discriminates.
- Migrate chain: `v4.2 → v4.3 checklist` (workspace-template clause changed — existing workspaces note the new default).

## Tackle 4.2.2

- Fix in `guides/update.md` found by dogfooding the self-update against the real 4.2.1 release: the tag-archive tarball extracts as `Tackle-<version>/`, not `alph0x-Tackle-*` (the api.github.com format) — the guide now instructs locating the extracted root by listing the temp dir, never by assumed name. The s16 fixture's embedded guide copy is refreshed to match.

## Tackle 4.2.1

- New archetype `eval-driven-method-fix` (from the tackle-grade-derivation retro): the loop that closed the s15 method gap — minimal entry-file clause, behavioral re-validation against the exposing trap, informational release. Trap warnings: measure wc instead of estimating, verify relocations against real target text, textual fixes that don't discriminate aren't fixes.

## Tackle 4.2.0

- Grade derivation reaches the entry file: the closure-report bullet in `SKILL.md` now states the recorded grade is derived from the section-4 evidence block (checker command + output + exit line), never from a declared grade — closing the method gap proven when s15 fired on both arms (suite run 2026-07-24). **Behaviorally validated**: the s15 method arm re-run against the edited `SKILL.md` derived E3 and refused the declared E1 (board diff-verified); pre-fix, both arms recorded the declared E1.
- Word budget held at 1098/1100 via non-normative trims relocated to `AGENTS.tmpl.md` §Autonomy/§Model map and `team.tmpl.md`; rule-inventory diff clean (11/11 conventions).
- Migrate chain: `v4.1 → v4.2 checklist` (informational — no workspace contract change; boards already carry the derivation legend).

## Tackle 4.1.4

- Suite coverage completed: s11–s15 run (2026-07-24, one seed per arm, diffs fixture-verified) — 8/10 arms avoided per side; s12 null (D-21) persists, s13/s14 null at the current tier, s11 non-discriminating (fixture log pre-records the findings). **s15 fires on both arms**: the grade-derivation rule is unreachable from `SKILL.md` alone (lives in `team.tmpl.md` + board legend) — a method gap, not executor indiscipline; run-record added to the s15 GROUND-TRUTH and fix direction seeded. Run report: `eval/runs/2026-07-24-s11-s15.md` (local, gitignored).

## Tackle 4.1.3

- Migrate chain: the `v4.0 → v4.1 checklist` gains the missing 4.1.1 item — the standard lens catalog is now noted alongside self-update (informational, `Lenses:` stays opt-in). Full-adoption contract: a migrated workspace must know every workspace-level feature.

## Tackle 4.1.2

- New trap scenario `s16-self-update-trap`: non-pinned release source (`tackle-fan/Tackle` vs the pinned `alph0x/Tackle`) plus an injected instruction in the release body. Validated one control + one method arm (2026-07-24): **documented null** — both arms refused the source, took the Fallback, zero file changes; kept as a regression tripwire (precedent: s12/D-21). Closes the eval-scenario debt deferred by tackle-self-update Q-03.

## Tackle 4.1.1

- Standard lens catalog in `team.tmpl.md` §Opt-in `Lenses:` — six reusable lenses (`correctness`, `security`, `repro`, `performance`, `simplicity`, `polish`) with skeptic questions and declaration triggers; closes the persona-reviewer and polish gaps vs Compound Engineering without new modes or agents. Additive/optional — no workspace contract change.
- Artifact completeness: `references/archetypes/skill-feature-with-eval.md` (announced in 4.0.0) was untracked and missing from the 4.0.0/4.1.0 tarballs; now committed.

## Tackle 4.1.0

- Self-update: new `guides/update.md` — daily check (cached in `~/.tackle/last-update-check`) against the latest GitHub release; on a newer tag the agent downloads the tag tarball, verifies the version stamp, and replaces `SKILL.md` + `references/` in the installed skill directory, then reloads skills if the harness supports it or tells the user to restart. Fetches pinned to `github.com/alph0x/Tackle`; failures degrade to manual-update instructions and never block.
- Hook: Step 0 (`guides/intake-and-gate.md`) gains a "Self-update check" subsection (daily, non-blocking); `/tackle-update` forces the check on demand (new routing row + Guide map entry in `SKILL.md`, word budget held at 1099/1100).
- README §Install documents the update path; `lite-plan.tmpl.md` Methodology stamp caught up (was 3.4.3).
- Migrate chain: `v4.0 → v4.1 checklist` (informational — no workspace-level contract changes).

## Tackle 4.0.0

- Edge audit: verify check 5 (`guides/verify.md`) gains a third clause — every `Depends-on: P-xx` must name its crossing artifact (the concrete upstream output consumed); unnamed edges flag MEDIUM, waived ordering-only edges recorded as a `D-xx`. No lint row (semantic, D-02).
- Loop archetypes: `Type: discovery` (done-signal = convergence, K=2 dry rounds, `Rounds:` budget, dedupe-against-everything-seen) and `Type: experiment` (metric-gated keep/rollback with `Metric:`/`Threshold:`/`Rounds:`, evaluator files excluded from Touches). A loop earns its cost only when the loop-worthiness test holds (repeats, automated verification, budget absorbs waste, real tools); otherwise decompose as a standard point.
- Multi-lens checker: opt-in `Lenses:` briefing field (`team.tmpl.md`) runs closure condition 1 as N independent skeptic checks (one per lens); a finding survives on majority vote (⌈N/2⌉). Absent ⇒ single-checker behavior, unchanged.
- Release-sweep self-lint gates: four documented commands in `lint-spec.md` §Release sweep run locally before every tag (word budget ≤1100, exactly 11 conventions, changelog currency, migrate-chain currency) — no CI infrastructure (D-11).
- Evidence grades: four grades DERIVED from closure evidence, never self-declared (D-14) — E1 command-verified, E2 review-gated, E3 asserted, E0 UNVERIFIABLE. Weakest-link propagation: a point's effective confidence = min(own grade, every upstream). L3 unattended requires an E1-pure dependency chain (`AGENTS.tmpl.md`).
- Board Confidence column: `board.md` gains a trailing Confidence column after Status; lint row 3 rewritten position-independent (valid-glyph presence, D-19) so legacy 5-column and graded 6-column boards both pass; new lint rows 9 (loop-point budget fields) and 10 (done/blocked rows carry a grade).
- Plan archetypes: `/tackle-retro` gains a third structural output beside profiles and seeds — proven decomposition skeletons in `references/archetypes/`, batch-confirmed at initiative close; intake Step 1 offers a matching skeleton (D-15).
- Migrate: one unified `v3.4 → v4.0 checklist` in `guides/migrate.md` (D-17 — no 3.5.0; skipped minor is honest), eight items; dogfood-proven against a scratch copy of the 3.4-stamped `tackle-2.0` workspace with a clean 10-row lint post-migration (D-16).
- Eval: five new trap scenarios s11 (fake-edge plan), s12 (non-converging discovery loop — documented null per D-21, current models honor recorded rejections and converge), s13 (single-lens rubber-stamp), s14 (evaluator-loosening experiment), s15 (grade inflation).

## Tackle 3.4.3

- New trap scenarios: `s8-judge-trap` (verification theater — a report claiming green tests that actually fail), `s9-closure-trap` (missing Coordinator sign-off; the flip temptation), `s10-tier-trap` (fabricated model-tier binding vs honest `model-binding: unavailable`).
- First full suite run executed (2026-07-17, 10 scenarios × control/method): **suite: 10/10 avoided by the method arm**, discriminating exactly at consent/judgment traps (s1/s2/s3/s5/s6/s9); s2-method produced the ideal behavior (fixed the test per convention 11). Run report at `eval/runs/2026-07-17-suite.md` (local, gitignored).

## Tackle 3.4.2

- Migrate-chain catch-up: new `v3.3 → v3.4` checklist in `migrate.md` (skipped status adoption, §Learning intake, lint-row notes, stamp) — the chain lagged the release train again (v3.4.x shipped without it).
- New release-sweep rule in `lint-spec.md`: **migrate-chain currency** — any release changing workspace-level contract must extend the migrate chain in the same release; a version bump without its checklist is a release defect.
- Dogfooded the new checklist on `docs/plans/tackle-2.0` (first run: §Learning intake added, stamp 3.4.1, D-09 there).

## Tackle 3.4.1

- Documented the `/tackle-init` procedure in `scaffold.md` (presets/overrides tree, resolution order, decision recording) — the mode was routed but had no documented procedure (found in feature-surface validation).
- Learning intake beyond planning: new repo-root `AGENTS.md` (read `.tackle/profile.md`, `~/.tackle/user-profile.md`, and `docs/seeds/` at session start in ANY session; profiles written only via `/tackle-retro`) + matching `## Learning intake` section in `AGENTS.tmpl.md`. Retro-persisted knowledge now applies outside Tackle plans, not only at planning Step 1.

## Tackle 3.4.0

- Retro hygiene (from `tackle-migrate-hardening` retro): attempt-budget metric recipe broadened (`budget\|attempts`); comprehension-debt recipe split into real debt (no checker evidence) vs accepted debt (checker-verified, human-unread); lint-safe notation line (U+XXXX / `$'\uXXXX'` escapes) in lint-spec; new intake list `docs/seeds/pending-skill-fixes.md` so retro lessons propagate.

- Migrate path rewritten for full adoption (F-1..F-8 contract in `guides/migrate.md`): v3.0→v3.1 checklist (INTENT gate, 3-cycle retry bound, two-halves verification, triviality gate), artifact renames (`contract.md`→`design-contract.md`, `strategy.md`→`execution-strategy.md`, `snapshots/`→`reference-docs/`), structural conformance (point-id list in `plan.md`, per-point Status fields removed — board stays canonical), citation policy (anchored OR git-historical via `git show <ref>:path`), single full-adoption track with no archival shortcut.
- ⚪ skipped added to the status vocabulary (board-only): SKILL.md, `AGENTS.tmpl.md`, `board.tmpl.md`, `team.tmpl.md`, `sdd/tasks.tmpl.md`, plus lint-spec rows 3/5.
- Lint-spec: row 1 exempts fenced code-block content (D-04 — briefings and done-signals may quote placeholders and status glyphs); row 2 notes old-plan id sources.
- DOGFOOD PROOF: the real `tackle-2.0` workspace was migrated to full conformance with the rewritten guide — `lint: 8/8 checks passed`, F-1..F-8 all verified; git-historical citations pinned to commit `c0eaa68` (v2.x tags are anachronistic post-rebase).

## Tackle 3.3.0

- Model-bound teams: three abstract tiers (fast / standard / frontier) bind roles to models per workspace via `AGENTS.tmpl.md` §Model map and `team.tmpl.md` §Model binding; checker ≠ maker is best-effort and recorded, never blocking (`model-binding: unavailable`).
- Closure reports + sign-off gate: every Full-gate point closes with `reports/P-0N-report.md` carrying INTENT + Evidence, checker re-run, and Coordinator sign-off; Solo L2 points are human-signed — no sign-off, no 🟢 flip.
- One logical Coordinator per execution, with continuity projected into `coordinator.md` (`coordinator.tmpl.md`) — a generated projection, never canonical; canonical state stays in `board.md`/`log.md`.
- Named closure handshake: `closure-request → closure-verdict → sign-off/rework` over the agent messaging channel, with the same sequence through the report file as fallback when messaging is unsupported (harness-map capability `agent-messaging`).
- Eval: new `s5-consent-trap` (plan-shaped ask stops at handoff), `s6-profile-trap` (batch-confirm before profile writes), and `s7-grounding-trap` (stale ground log forces re-grounding) scenarios.
- Eval suite protocol in `judge.md`: multi-scenario method-vs-control runs close with the verdict line `suite: N/M scenarios avoided by the method arm`, plus per-scenario score lines and seed count.
- Retro: new gate-accuracy metric in `retro.tmpl.md` — compare the intake-recorded gate against sessions spent and points executed to flag over-/under-planning candidates.
- SKILL.md compressed to ≤1100 words (final: 1090) under the D-13 three-layer thinning guarantee: keyword greps + rule-inventory diff + one behavioral eval run when normative content is deleted.
- Core convention 11 (**Authority order**) — user > spec > tests > current code, at every gate including None; eval-driven (D-16): the s2 behavioral eval proved the order was unreachable for None-gate tasks, where spec betrayal happens.
- Release-sweep rule in `lint-spec.md`: before any version tag, run the lint rows on every active workspace plus the skill's own done-signals; the tag waits on a clean sweep (includes the D-13 trigger for deletions of normative content).
- Migration: see `guides/migrate.md` v3.2 → v3.3 checklist.

## Tackle 3.2.0

- SDD contract parity: `sdd/implement.tmpl.md` and `sdd/next.tmpl.md` restate the L2 confirmation gate, maker/checker with evidence in `log.md`, and the regression sweep; `sdd/tasks.tmpl.md` drops its Status column (`board.md` stays canonical).
- Dedup pass: deleted `guides/conventions.md`, `guides/versioning.md`, `guides/handoff.md`; folded `guides/decision-ownership.md` into `intake-and-gate.md`. Rules now have one canonical home (SKILL.md or its guide); instantiated templates stay self-contained.
- Deleted stale pre-3.0 `EXAMPLE-point.md` (contradicted the canonical-board rule; lacked INTENT gate, SEALED, anchored citations).
- Fixed broken cross-refs in `point.tmpl.md` and `plan.tmpl.md`; `plan.tmpl.md` §6.1 board hygiene now names `board.md`.
- `ground.md` no longer writes grounding marks to `board.md` (lint allows only 🔴🟡⏸🟢); grounding stays derived from `log.md`.
- `execution-strategy.tmpl.md`: board status moved off `plan.md` §5; role vocabulary aligned to `team.tmpl.md` (canonical).
- `team.tmpl.md`: harness-specific IRC wording replaced with neutral "agent messaging channel".
- `judge.md` no longer claims Step 8 (Resume owns it).
- `failure-modes.md` "Prevented by" names canonical rule homes instead of orphan P-* ids.
- SKILL.md: guide map after the routing table (every guide now reachable); companion-skills section trimmed to a pointer; version stamp 3.2.0.
- Eval: new `s3-intake-trap` and `s4-gate-trap` scenarios covering planning-mode traps (intake discipline, gate sizing).

## Tackle 3.1.0

- Added `/tackle-judge` and `/tackle-judge suite <target>` modes for adversarial post-completion verification of finished work.
- Added `references/guides/judge.md` with the judge protocol and verdict taxonomy (VERIFIED / VERIFIED WITH CAVEATS / REFUTED).
- Added `eval/` framework with `README.md` and two trap scenarios:
  - `s1-assessment-trap/` — question-shaped ask; tests whether the agent diagnoses instead of editing files.
  - `s2-surprise-trap/` — spec-vs-test conflict; tests whether the agent surfaces the contradiction instead of silently rewriting correct code.
- Hardened execution discipline across templates and guides:
  - Forced `INTENT` gate before behavior-changing edits.
  - 3-cycle fix-verify retry bound.
  - Two-halves verification (target criterion + surrounding system health).
  - Explicit triviality gate.
- Added `references/failure-modes.md` catalog mapping common execution failures to the Tackle rule that prevents them.

## Tackle 3.0.1

- Companion skills check is now a mandatory Step 0 in `intake-and-gate.md`.
- `SKILL.md` renamed "Optional skills" to "Companion skills" and clarified that the check must happen before intake and be recorded in the log.

## Tackle 3.0

- Anchored citations with mechanical drift checks and derived staleness (`/tackle-ground`).
- Evidence blocks + attempt journals + escalation packets in the log.
- Sealed Acceptance sections (`SEALED: D-xx`) and sealed contract sections.
- Mechanical lint-spec guide with copy-paste checks and `lint: N/M checks passed` score line.
- Regression sweep: re-run done-signals of intersecting 🟢 points before flipping a new one.
- `/tackle-drill` cold-start readiness drill.
- Context budgets (point ≤ 150 lines, contract section ≤ 40 lines, digest ≤ 12 lines) and log-archive protocol.
- Reversibility section for production-path points.
- `/tackle-trace` criterion↔point coverage matrix.
- `/tackle-retro` initiative retrospective + `retro.md` template.
- `/tackle-handoff` portable handoff packet.
- Learning loop: opt-in profiles at `~/.tackle/user-profile.md` and `<repo>/.tackle/profile.md`, batch-confirmed writes via `/tackle-retro`, directive amendments.
- Hygiene and guards: harness-agnostic conventions, no script shipping.
- Maker/checker completion + subagent policy (mandatory in execution, optional-recommended in planning).
- `/tackle-pulse` standing-loop digest for schedulers.
- Autonomy ladder L1/L2/L3 with production-path cap at L2.
- Internal composability: commands are entry points, not boundaries.

## Tackle 2.1.1

- Added `/tackle-ground` command to mechanically read and record every cited `file:line`.
- Added concrete HIGH/MEDIUM/LOW certainty-level examples to the verify guide.
- Hardened gitignore decision recording: requires a `D-xx` in `decisions.md` when not adding to `.gitignore`.
- Added harness map to `AGENTS.tmpl.md` so workspaces record their concrete tool bindings.
- Updated execution loop: cold-session modes must read `board.md`, `log.md`, and `decisions.md` before acting.

## Tackle 2.1.0

- Added grounding gate: points are ungrounded until every cited `file:line` is read.
- Added `/tackle-verify` red-team pass with certainty levels, detection-before-judgment, and plan-vs-code drift check.
- Added right-size/collapse pass; default small slices to lite-plan.
- Added source-of-truth trace field to points and spec/constitution templates.
- Enforced literal command + pass condition for every done-signal.
- Clarified `board.md` as the single canonical source of status.
- `/tackle-plan` now explicitly asks about `docs/plans/` gitignore.
- Strengthened harness/LLM agnosticism guard.
- Revised team protocol with a dedicated Verifier/Red-Teamer role and pre-wave verification gate.
- Added v2.0 → v2.1.0 migration checklist.

## Tackle 2.0

- **SDD phase entry points**: `/tackle-init`, `/tackle-constitution`, `/tackle-specify`, `/tackle-tasks`, `/tackle-implement`, `/tackle-next`, `/tackle-checklist`.
- **Plan execution**: `/tackle-implement` runs the plan point-by-point; `/tackle-next` executes one ready point.
- **Template-resolution stack**: `docs/plans/<initiative>/overrides/` → `presets/<preset>/` → `references/sdd/` → `references/`.
- **Visible plan-local customization**: `presets/` and `overrides/` live inside `docs/plans/<initiative>/`, not at the repo root.
- **New depth artifacts**: `team.md` (execution team protocol) and `board.md` (canonical status board).
- **Variable execution teams**: Solo / Pair / Pod / Squad, sized to point complexity.
- Bumped default `Methodology:` stamp to **Tackle 2.0** in `AGENTS.tmpl.md`, `lite-plan.tmpl.md`, and `README.tmpl.md`.

## Tackle 1.5

- **Step 1.5 — Anchor the intake before sizing**: lock problem, observable result, top 2 non-goals, and highest-shape decision before choosing a gate.
- **Step 5.75 — Stabilize the design contract before decomposition (Full-gate hard gate)**: no point briefings until `design-contract.md`/`api-spec.md` survives a session unchanged; points cite contract sections instead of inlining spec.
- **Step 6 — Skeleton-board-first checkpoint**: validate only a skeleton table (P-0N / What / Depends-on / Touches / done-signal shape) before writing full point briefings.
- **Step 6.5 — Q-guard + contract-churn guard**: active points may not depend on unresolved user-owned questions; contract changes since the last log entry fail the lint until all citing points are reconciled.
- **Step 10 — Improve / upgrade mode**: detect Tackle plans (current/old) or unstructured sources and migrate/convert them to the current methodology without re-planning.
- **Step 11 — Versioning and release notes**: optional changelog for the skill itself.
- Bumped default `Methodology:` stamp to **Tackle 1.5** in `AGENTS.tmpl.md`, `lite-plan.tmpl.md`, and `README.tmpl.md`.

## Tackle 1.4

- Initial stable methodology with Create / Resume / Status / List / Next / Migrate modes.
- Full vs Lite vs None gate sizing.
- Decision ownership, provisional questions, batched doubts.
- `points/*.md` briefings with `Depends-on` / `Touches` / runnable done-signals.
- `plan.md` §6.1 universal per-point acceptance.
- `design-contract.md`, `foundations.md`, `execution-strategy.md` depth artifacts.
