# Execution strategy — how to attack the points

> **Full-gate depth artifact (optional).** Create this when execution will span multiple
> agents/sessions in parallel, or when the points fall into phases with quality bars between
> them. For a short linear plan (do P-01, then P-02, then done), the dependency graph in
> `plan.md` §5 is already the strategy — skip this file.
>
> **Tackle still does NOT execute.** This artifact *plans the attack*; the waves run later,
> in separate sessions. It is harness-agnostic — it names roles (orchestrator / implementer /
> reviewer), not vendor tools. Use whatever parallel-agent, isolation and review facilities
> your environment provides; do the rest sequentially by hand.

## Roles

- **Orchestrator** — drives waves, relays review findings, merges in dependency order, keeps
  the board (`plan.md` §5) + `log.md` current. **Never implements.**
- **Implementer** — one per point, briefed with the point's ready-to-paste starting prompt.
  Decomposition is built to run **several implementers in parallel** (Step 6) — the orchestrator
  launches a fan-out wave in one batch.
- **Code-quality guardian** — reviews *within-unit* quality before a point flips 🟢: smells,
  redundancy, DRY, SOLID, self-documenting code, naming, AND conformance to the point's
  acceptance + design-contract section. Runs per point (or per class when a point creates ≥2
  public types). It **loops with the implementer who wrote the code** (kept alive — messaging
  beats re-briefing) until clean; it drives the author, it does not rewrite. The **inter-wave
  gate** (below) is the complement: it owns what only shows in the *merged* tree — cross-unit
  drift, races, duplication between points.

## Pre-wave verification gate (BLOCKING)

Before any wave starts, run `/tackle-verify` on every point in the wave. A point with HIGH findings is removed from the wave and returned to planning. MEDIUM findings require explicit user acceptance; LOW findings become notes for the Driver.

This gate runs once per wave, not per point, so parallel-ready points are verified in batch.

## Waves (derived from the dependency graph)

Group the points into waves: everything with no unmet dependency runs in one wave; the next
wave waits on the gate. Each point runs as a loop — its **done-signal** (in the briefing) is the
loop's exit check, its **iteration budget** the stop-and-escalate rule. Use each point's
**Touches (write scope)** to assign worktrees: points with disjoint scopes run as concurrent
loops safely; overlapping scopes need isolated worktrees (if supported) or serialize.
`board.md` and `log.md` are written only in the main tree, only by the orchestrator;
implementer worktrees carry code, never state files.

```
Wave 1 (sequential):  {{P-01 ──► P-02}}        {{foundation}}
        ── QUALITY GATE ──
Wave 2 (parallel):    {{P-03 ∥ P-04}}          {{...}}
        ── QUALITY GATE ──
Wave N (human):       {{P-0x}}                  {{anything needing hardware / a person}}

Deferred (gated on a question): {{P-0y blocked on Q-0z — do not start until resolved}}
```

## The quality gate (between waves, BLOCKING)

After a wave's points merge and before the next wave starts, run ONE gate over the **merged**
tree (per-point reviewers see one point; the gate sees the whole, where drift and races live):

0. **Verification re-check** — re-run `/tackle-verify` on the merged diff; new drift or broken claims block the next wave.
1. **Run the checks, don't read them** — the suite is green; stability holds (repeat ×N under
   a hard timeout; a hang = fail); concurrency is race-clean if the env has a checker.
2. **Fundamentals** — DRY, no smells, the dependency rule holds, naming per the project's
   guidelines, public surface documented.
3. **Grounding** (if `foundations.md` exists) — every new abstraction in the wave's diff has
   its decision→principle→source row.
4. **Contract & hygiene** (if `design-contract.md` exists) — implemented surface matches it,
   or the spec was superseded first; the board + log are current.

**Verdict** → `PASS` (next wave launches) · `PASS-WITH-NOTES` (launches; notes become TODOs on
the next wave) · `FAIL` (next wave blocked; findings route back to the owning point).

## Deferral

A point gated on an open `Q-xx` is **not** in the wave plan until the question resolves — list
it under *Deferred* with the blocking `Q-id`, not as a 🔴 in an active wave. Don't plan work
behind an unanswered external dependency.

## Orchestration notes

- Keep an implementer alive through its review-fix loop (context retention beats re-briefing);
  spawn fresh agents only across waves.
- Resist over-orchestration on small initiatives — collapse to a single sequential session;
  the self-contained briefings support both modes.
- Board discipline after every wave: a finished wave with a stale board is a broken handoff.
