# Tackle learning-loop profile — project

**Scope:** project → `<repo>/.tackle/profile.md`

**Evolution:** enabled (2026-07-16)

A profile stores hypotheses and directives distilled from retros. It is read during intake and updated only during `/tackle-retro`. Nothing here is ever written silently.

## Rules

- **Single write path**: `/tackle-retro` is the only command that writes to this file.
- **Batch-confirmed**: every candidate is confirmed by the user before it is recorded.
- **Top-K limit**: only the top ≤ 10 entries by confidence enter a session.
- **Conflict resolution**: project directives outrank user directives when both apply.
- **Retired, not deleted**: entries with `status: retired` are kept for audit; they are never removed.
- **Opt-out anytime**: a "pause" flips the Evolution header but keeps counters; a "purge" deletes the file.

## Hypotheses

- This repo prefers done-signals as grep commands with literal pass conditions over prose criteria · confidence: 0.9 · evidence: 10✓/0✗ (tackle-2.1.1-friction, tackle-3.2.0-review, tackle-model-teams, tackle-migrate-hardening, tackle-graph-execution — every 4.0.0 point; tackle-self-update ds1–ds7; tackle-lens-catalog ds; tackle-grade-derivation ds; tackle-testing-doctrine; tackle-universal-update-check) · status: active · from: tackle-3.2.0-review, 2026-07-16; reinforced: tackle-migrate-hardening, 2026-07-17; tackle-graph-execution, 2026-07-20; tackle-self-update, 2026-07-24; tackle-lens-catalog, 2026-07-24; tackle-grade-derivation, 2026-07-24; tackle-testing-doctrine, 2026-07-30; tackle-universal-update-check, 2026-07-30
- Behavioral trap evals and dogfood runs must gate changes that delete normative content or rewrite methodology flows (keywords prove words, inventory proves rules, only behavior proves behavior) · confidence: 0.8 · evidence: 5✓/0✗ (tackle-model-teams D-13/D-16 s2 4-arm eval; tackle-migrate-hardening P-04 dogfood migration; tackle-grade-derivation — s15 method-arm re-run; tackle-testing-doctrine — s17; tackle-universal-update-check — s18) · status: active · from: tackle-model-teams, 2026-07-16; reinforced: tackle-migrate-hardening, 2026-07-17; tackle-graph-execution, 2026-07-20; tackle-grade-derivation, 2026-07-24; tackle-testing-doctrine, 2026-07-30; tackle-universal-update-check, 2026-07-30
- Contract claims about mechanical tool behavior (awk field indexing, grep flags) must be fixture-tested at planning, not asserted · confidence: 0.7 · evidence: 4✓/0✗ (tackle-graph-execution D-14 `$(NF-1)` row-3 break → D-19; tackle-self-update D-03 `curl -L` vs `curl -sL`; tackle-testing-doctrine — done-signals run before seal; tackle-universal-update-check — same, plus pre-counted word-budget arithmetic held exactly) · status: active · from: tackle-graph-execution, 2026-07-20; reinforced: tackle-self-update, 2026-07-24; tackle-testing-doctrine, 2026-07-30; tackle-universal-update-check, 2026-07-30
- Anchored `file:NN` citations into guides the initiative itself edits drift per wave; prefer fragment/section anchors or budget a per-wave re-ground · confidence: 0.6 · evidence: 1✓/0✗ (tackle-graph-execution row-4 drift at 3 wave boundaries) · status: active · from: tackle-graph-execution, 2026-07-20
- Seal a behavioral trap's fire-requirement only after validating the trap against the real executor tier · confidence: 0.5 · evidence: 1✓/0✗ (tackle-graph-execution s12 null — 6 seeds/2 tiers avoided the trap → D-21) · status: active · from: tackle-graph-execution, 2026-07-20
- Planning a release point reads `lint-spec.md` §Release sweep in full (all 4 self-lint gates) — migrate-chain currency shapes scope even when D-13 doesn't trigger · confidence: 0.7 · evidence: 5✓/0✗ (tackle-self-update D-05 — gate 4 surfaced mid-execution, unplanned; tackle-lens-catalog — gate 4 pre-verified; tackle-grade-derivation — v4.1 → v4.2 checklist at planning; tackle-testing-doctrine — v4.2 → v4.3 + D-13 non-trigger reasoned; tackle-universal-update-check — patch gate-4 pre-verified against existing checklist) · status: active · from: tackle-self-update, 2026-07-24; reinforced: tackle-lens-catalog, 2026-07-24; tackle-grade-derivation, 2026-07-24; tackle-testing-doctrine, 2026-07-30; tackle-universal-update-check, 2026-07-30
- Features for the Tackle skill are planned and executed through Tackle itself (dogfood), even Lite-sized ones · confidence: 0.7 · evidence: 5✓/0✗ (tackle-self-update — explicit user redirect; tackle-lens-catalog — Lite at intake; tackle-grade-derivation — Lite; tackle-testing-doctrine — Lite; tackle-universal-update-check — Lite, user-reported defect → fix → release in one session) · status: active · from: tackle-self-update, 2026-07-24; reinforced: tackle-lens-catalog, 2026-07-24; tackle-grade-derivation, 2026-07-24; tackle-testing-doctrine, 2026-07-30; tackle-universal-update-check, 2026-07-30
- A release's version-stamp edit travels in its own edit call aimed at `SKILL.md` — batched with CHANGELOG edits it gets mis-targeted at `references/CHANGELOG.md` · confidence: 0.7 · evidence: 5✓/0✗ (tackle-self-update release; tackle-lens-catalog release — identical slip both times; tackle-grade-derivation release — own call, clean; tackle-testing-doctrine release — own call, clean; tackle-universal-update-check release — own call, clean) · status: active · from: tackle-lens-catalog retro, 2026-07-24; reinforced: tackle-grade-derivation, 2026-07-24; tackle-testing-doctrine, 2026-07-30; tackle-universal-update-check, 2026-07-30
- A method gap exposed by a trap scenario is closed in the entry file and validated by re-running that trap against the edited file (behavior over text) · confidence: 0.6 · evidence: 3✓/0✗ (tackle-grade-derivation — s15 0/2 pre-fix, E3 post-fix; tackle-testing-doctrine — s17 method test-first; tackle-universal-update-check — s18 method ran the check on resume) · status: active · from: tackle-grade-derivation retro, 2026-07-24; reinforced: tackle-testing-doctrine, 2026-07-30; tackle-universal-update-check, 2026-07-30

## Hypotheses (added 2026-07-30)

- A trap eval over a single-clause change needs 1 seed/arm; scale seeds only when the first run is ambiguous · confidence: 0.6 · evidence: 2✓/0✗ (tackle-testing-doctrine s17 — method test-first vs control implementation-first; tackle-universal-update-check s18 — method ran the check vs control straight-to-fixture) · status: active · from: tackle-testing-doctrine, 2026-07-30; reinforced: tackle-universal-update-check, 2026-07-30
- A workspace whose board is all-green counts as closed for release-sweep scope, even with accumulated row-4 citation drift — re-ground belongs to a cleanup initiative if the workspace reopens · confidence: 0.5 · evidence: 1✓/0✗ (tackle-testing-doctrine D-03 — graph-execution 12🟢/0🟡/0🔴 with 5 pre-existing stale citations, waived at the 4.3.0 sweep) · status: active · from: tackle-testing-doctrine, 2026-07-30
- Trap gates are sealed on host-independent observables (e.g. the cache-file *read*, not the fetch) and declared in the GROUND-TRUTH before the run — verdicts stay unambiguous on any host state · confidence: 0.5 · evidence: 1✓/0✗ (tackle-universal-update-check s18 — gate = the read; host cache carried today's date and the method arm's read-then-stop still passed cleanly) · status: active · from: tackle-universal-update-check, 2026-07-30

## Directives

- none
