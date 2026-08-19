# skill-feature-with-eval

**Summary** — ship a normative skill feature end to end: core edit (template/guide) + mechanical lint support + a behavioral trap scenario + a migrate-chain entry (dogfood-proven) + a gated release. Fits any change that adds a rule or field to a methodology/skill and must prove it behaviorally, not just textually.

## Point list

- **core** — edit the template/guide that introduces the feature (the field, clause, or section). One responsibility, grep-able done-signal.
- **lint-support** — add the mechanical row that enforces the feature's structural invariant (pipe-free, copy-paste, 0-lines-of-output pass).
- **eval-scenario** — a trap fixture (README + GROUND-TRUTH + fixtures) proving the feature behaviorally; run a control arm against the pre-feature baseline to confirm it discriminates.
- **migrate-checklist** — the version→version adoption checklist, executed (dogfood) against a copy of a real old workspace with a clean lint post-migration.
- **release** — stamps + changelog + release sweep + D-13 gate (rule-inventory diff + method-arm eval).

## Edge pattern

`core → lint-support`; `{core, lint-support, eval-scenario} → migrate-checklist`; `all → release`. Cores of independent features are mutually parallel (disjoint Touches).

## Wave shape

Independent feature cores fan out in wave 1 (∥, disjoint Touches); lint-support and eval-scenario mid; migrate-checklist + docs late; release last, alone. Reserve the release point as the longest single unit (it runs every method arm by hand).

## Trap warnings

- **Citation drift**: points that edit the same guides they cite shift line numbers — expect a per-wave re-ground, or cite by fragment/section not `file:NN`. Hardened (tackle-crux-grounding, 2026-08-12): the feature's own wave edits drift the very citations the plan cites — **re-anchor at every wave gate**, not only at ground time; once the fix ships (e.g. `tackle-check ground`), **dogfood it on the plan's own drift** at the wave close. Both waves of tackle-crux-grounding drifted their own citations (guide edits; eval/README.md registration).
- **Assert-vs-test**: any contract claim about mechanical tool behavior (awk field indexing, grep flags) must be fixture-tested at planning; asserting it ships a latent break (cost one supersede when caught at execution).
- **Obsolete traps**: validate a behavioral scenario against the real executor tier before sealing an acceptance that requires it to fire — a trap models may no longer fall for burns budget.
- **Judge-role trap nulls**: when the destination guide is part of the fixture (fixture-as-install), a no-skill control can reach the discriminating rule by reading the in-repo protocol — expect a null and keep the scenario as a regression guard. The discriminating signal is the guide-owned *specific* (threshold line, exact format), not the general behavior (s37/s39, graft-takeaways 2026-08-18).
- **Portable gates**: sealed done-signals must use lowest-common-denominator tooling (`grep -l`, not `grep -lc`) — flag behavior varies by host.
- **Independent checkers pay for themselves**: on this shape they caught three defects (a broken lint field-index, an obsolete trap, a non-portable gate) before any green flip; a 4th cycle (tackle-5.0.1-hotfix) added two more advisory-driven catches (the update.md delivery-channel gap and a gate-5 `head -1` blind spot) that the process itself missed. Signal/ruido note (5.0.2): as the process catches up with the checker, the value shifts from catching gaps to catching drift-in-claims — advisories become nits on already-covered ground, which is the checkpoint to watch.
- **Self-referential done-signals**: a briefing that declares `**Run**: sh tackle-check done-signal <same briefing>` recurses without a base case when the executor extracts ALL Run lines (P-01 fork bomb, 2026-08-03). Never declare machine-run over the point that declares it — keep such demos checker-verified/manual, and guard the executor with an explicit FAIL for self-reference.
- **Machine-run checks must fail on empty output**: `git ls-remote --tags` exits 0 even with no tag (empty output) — as a done-signal it passes spuriously. A mechanical gate needs a real failure condition (grep the output), not just exit-code trust.
- **Last-mile dogfood**: the release gate is the feature's final self-test — dogfood the new gate on the release that ships it. Tackle-sweep-gate (2026-08-13): the sweep's first green run was vacuous on the workspace dimension (paths resolved relative to cwd, globs found nothing, every workspace linted "clean") — the planted DS4 fixture workspace caught it, not the green; and gate 7 flagged the README migrate-row lagging the 5.4.0 stamp bump mid-release, which the stamp gate would have passed. A composition gate needs a planted-failure fixture per loop it runs, and derived-value checks fire on the very release that ships them.

## Lite scaling

The skeleton scales down to a 3-point Lite plan when the feature adds no mechanically verifiable structural invariant: **core → eval-scenario → release**, dropping lint-support and folding migrate-checklist into release (gate 4 of the release sweep forces the checklist anyway). Proven by tackle-testing-doctrine (2026-07-30): trap warnings still apply in full — cite by section, fixture-test fragments, portable gates.

## Provenance

tackle-graph-execution (Tackle 4.0.0), 2026-07-20. Retro: `docs/plans/tackle-graph-execution/retro.md`. Eligibility caveat: the source graph was re-shaped post-seal (scope grew CI hook + 4.0.0 + single-release renumber); the FINAL shape distilled here is what proved stable through execution. Re-confirmed 6×: tackle-model-teams, tackle-testing-doctrine (Lite scaling), tackle-universal-update-check (Lite), tackle-slim-and-traps (Lite), tackle-5.0-self-verify (Full, 2026-08-03 — s23-flip-gate as the D-13 behavioral arm, double-gate contract change), graft-takeaways (Full, 2026-08-18 — three traps as the D-13 behavioral arms; 5 independent adoptions fanned as P-01→P-02 / P-03→P-04 sequenced on shared Touches, P-06 ∥).
