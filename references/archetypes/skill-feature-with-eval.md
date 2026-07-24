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

- **Citation drift**: points that edit the same guides they cite shift line numbers — expect a per-wave re-ground, or cite by fragment/section not `file:NN`.
- **Assert-vs-test**: any contract claim about mechanical tool behavior (awk field indexing, grep flags) must be fixture-tested at planning; asserting it ships a latent break (cost one supersede when caught at execution).
- **Obsolete traps**: validate a behavioral scenario against the real executor tier before sealing an acceptance that requires it to fire — a trap models may no longer fall for burns budget.
- **Portable gates**: sealed done-signals must use lowest-common-denominator tooling (`grep -l`, not `grep -lc`) — flag behavior varies by host.
- **Independent checkers pay for themselves**: on this shape they caught three defects (a broken lint field-index, an obsolete trap, a non-portable gate) before any green flip.

## Provenance

tackle-graph-execution (Tackle 4.0.0), 2026-07-20. Retro: `docs/plans/tackle-graph-execution/retro.md`. Eligibility caveat: the source graph was re-shaped post-seal (scope grew CI hook + 4.0.0 + single-release renumber); the FINAL shape distilled here is what proved stable through execution.
