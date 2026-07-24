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

- This repo prefers done-signals as grep commands with literal pass conditions over prose criteria · confidence: 0.9 · evidence: 8✓/0✗ (tackle-2.1.1-friction, tackle-3.2.0-review, tackle-model-teams, tackle-migrate-hardening, tackle-graph-execution — every 4.0.0 point; tackle-self-update ds1–ds7; tackle-lens-catalog ds; tackle-grade-derivation ds) · status: active · from: tackle-3.2.0-review, 2026-07-16; reinforced: tackle-migrate-hardening, 2026-07-17; tackle-graph-execution, 2026-07-20; tackle-self-update, 2026-07-24; tackle-lens-catalog, 2026-07-24; tackle-grade-derivation, 2026-07-24
- Behavioral trap evals and dogfood runs must gate changes that delete normative content or rewrite methodology flows (keywords prove words, inventory proves rules, only behavior proves behavior) · confidence: 0.8 · evidence: 3✓/0✗ (tackle-model-teams D-13/D-16 s2 4-arm eval; tackle-migrate-hardening P-04 dogfood migration as the migrate-guide behavioral test; tackle-grade-derivation — s15 method-arm re-run gated the new derivation clause) · status: active · from: tackle-model-teams, 2026-07-16; reinforced: tackle-migrate-hardening, 2026-07-17; tackle-graph-execution, 2026-07-20; tackle-grade-derivation, 2026-07-24
- Contract claims about mechanical tool behavior (awk field indexing, grep flags) must be fixture-tested at planning, not asserted · confidence: 0.7 · evidence: 2✓/0✗ (tackle-graph-execution D-14 `$(NF-1)` row-3 break, caught only at execution by a 6-column fixture → D-19; tackle-self-update D-03 — done-signal literal `curl -L` vs guide's `curl -sL`, caught at execution) · status: active · from: tackle-graph-execution, 2026-07-20; reinforced: tackle-self-update, 2026-07-24
- Anchored `file:NN` citations into guides the initiative itself edits drift per wave; prefer fragment/section anchors or budget a per-wave re-ground · confidence: 0.6 · evidence: 1✓/0✗ (tackle-graph-execution row-4 drift at 3 wave boundaries) · status: active · from: tackle-graph-execution, 2026-07-20
- Seal a behavioral trap's fire-requirement only after validating the trap against the real executor tier · confidence: 0.5 · evidence: 1✓/0✗ (tackle-graph-execution s12 null — 6 seeds/2 tiers avoided the trap → D-21) · status: active · from: tackle-graph-execution, 2026-07-20
- Planning a release point reads `lint-spec.md` §Release sweep in full (all 4 self-lint gates) — migrate-chain currency shapes scope even when D-13 doesn't trigger · confidence: 0.7 · evidence: 3✓/0✗ (tackle-self-update D-05 — gate 4 surfaced mid-execution, unplanned; tackle-lens-catalog — full sweep read at planning, gate 4 pre-verified, zero mid-flight surprises; tackle-grade-derivation — v4.1 → v4.2 checklist identified at planning) · status: active · from: tackle-self-update, 2026-07-24; reinforced: tackle-lens-catalog, 2026-07-24; tackle-grade-derivation, 2026-07-24
- Features for the Tackle skill are planned and executed through Tackle itself (dogfood), even Lite-sized ones · confidence: 0.7 · evidence: 3✓/0✗ (tackle-self-update — explicit user redirect to dogfood; tackle-lens-catalog — dogfooded Lite at intake without prompting; tackle-grade-derivation — Lite again) · status: active · from: tackle-self-update, 2026-07-24; reinforced: tackle-lens-catalog, 2026-07-24; tackle-grade-derivation, 2026-07-24
- A release's version-stamp edit travels in its own edit call aimed at `SKILL.md` — batched with CHANGELOG edits it gets mis-targeted at `references/CHANGELOG.md` · confidence: 0.7 · evidence: 3✓/0✗ (tackle-self-update release; tackle-lens-catalog release — identical slip both times; tackle-grade-derivation release — own call, clean) · status: active · from: tackle-lens-catalog retro, 2026-07-24; reinforced: tackle-grade-derivation, 2026-07-24
- A method gap exposed by a trap scenario is closed in the entry file and validated by re-running that trap against the edited file (behavior over text) · confidence: 0.6 · evidence: 1✓/0✗ (tackle-grade-derivation — s15 went 0/2 arms pre-fix, E3-derived post-fix) · status: active · from: tackle-grade-derivation retro, 2026-07-24

## Directives

- none
