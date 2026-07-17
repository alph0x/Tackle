# Point P-00 — Walking skeleton

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone. Links are for depth, not prerequisites — EXCEPT the `contract.md`
> §"States & transitions" this point probes, which IS required reading. Tackle plans this point;
> it does not implement it here.

## Status & wiring
**Depends on**: none · **Status**: ⚪ skipped (optional slice; executed as no-op because real phases were built directly).
- **Touches (write scope)**: `references/sdd/*.tmpl.md` (stub placeholders), a temporary router file under `references/` (would have been removed once real phases land), and a demo fixture under `docs/plans/tackle-2.0/_demo-walking-skeleton/` (never created).

## Goal (single responsibility — one loop-completable change)
Create the thinnest end-to-end SDD flow so the chain can be demoed before any phase has real content: stub templates for `constitution`, `specify`, `tasks`, `implement`, `next`, and `checklist`, plus a temporary router that calls each stub in sequence. "Done" = a single command walks `/tackle-init` → `/tackle-constitution` → `/tackle-specify` → `/tackle-plan` → `/tackle-tasks` → `/tackle-implement` and produces the expected artifact at each step with no unfilled-template errors.

## Context (grounded)
- Tackle 2.0 introduces SDD phase entry points between intake and execution; see `contract.md` §"States & transitions" and `SKILL.md` lines 41–53.
- The real phase points (P-01 through P-05) implement production content for each entry point. A walking skeleton is useful when the team wants to validate the overall chain shape before committing to full template content.
- `board.md` lists P-00 as optional and explicitly skipped; P-01..P-05 were implemented directly instead, which satisfies the same end-to-end flow with real content.

## Non-goals
- Real constitution/spec content (that's P-01 and P-02).
- Real task decomposition or execution engine (that's P-03, P-04, and P-05).
- Template-resolution stack or presets (that's P-06 and P-07).
- Preserving the temporary router after real phases land.
- Becoming a dependency for any other point; P-01..P-05 do not require P-00.

## Recommended approach
1. Create minimal `references/sdd/{constitution,specify,tasks,implement,next,checklist}.tmpl.md` files with a single filled section and visible placeholders for the rest.
2. Add a temporary router (e.g., a short shell script or markdown checklist under `references/`) that invokes each phase trigger in order against a demo plan.
3. Run the router against `docs/plans/tackle-2.0/_demo-walking-skeleton/` and verify each artifact is produced.
4. Delete the router and replace stubs as P-01..P-05 land; do not keep the skeleton once real phases exist.

## Alternatives / fallbacks
- **If the team prefers real content over stubs** → skip P-00 and implement P-01..P-05 directly. This is the path that was taken; no artifacts from the walking skeleton remain.
- **If a demo is needed after real phases exist** → use `docs/plans/tackle-2.0/` itself as the demo target and run the real triggers; the skeleton adds no value.

## Recommended starting prompt
<!-- Ready to paste into a fresh session to attack this point. Keep it grounded and bounded. -->
```text
Resolve Point P-00 (Walking skeleton) of the "Tackle 2.0" plan.
Repo: ~/Developer/Tackle. Read points/P-00-walking-skeleton.md first; it is self-contained.
Do: create stub SDD phase templates under references/sdd/ and a temporary router that demos the full chain from /tackle-init through /tackle-implement against a throwaway plan.
Constraints: do not implement real phase content; do not create files outside references/ or the demo plan; delete the router once P-01..P-05 are green.
Acceptance: the router produces constitution.md, spec.md, plan.md, tasks.md, board.md updates, and log.md entries in order with no unfilled-template errors.
Loop until green: ./references/_demo-sdd-chain.sh
```

## Acceptance — the loop's exit gate
- **Done-signal**: `./references/_demo-sdd-chain.sh` → pass = exit 0 and the script asserts the artifact count and placeholder markers at each phase. Since P-00 is skipped, the equivalent verification is: `ls references/sdd/` contains `constitution.tmpl.md`, `specify.tmpl.md`, `tasks.tmpl.md`, `implement.tmpl.md`, `next.tmpl.md`, `checklist.tmpl.md` and `board.md` marks P-01 through P-05 as 🟢 done.
- [x] Meets the **universal per-point acceptance** in `plan.md` §6.1 (skipped; no code produced, no regression risk).
- [x] **Correctness** — the skipped status is recorded in `board.md` and the real SDD chain is verified by the done-signals of P-01..P-05.
- [x] No leftover walking-skeleton router or stub files remain in `references/` outside the real SDD templates.
- **If it fails →** if stub artifacts remain after P-01..P-05, delete them; if the board still shows P-00 as 🔴 or 🟡, update it to ⚪ skipped. Self-correct up to the workspace iteration budget (`AGENTS.md`), then STOP + escalate.

## Open questions for this point
- None. P-00 is a provisional optional slice; the decision to skip it is recorded in `strategy.md` and `board.md`.

## Definition of Ready (the gates that can FAIL)
- [x] **Single responsibility** — one change (stub the SDD chain), no "and".
- [x] **No open decisions inside it** — the decision to skip is closed and recorded.
- [x] **Loop-ready** — the done-signal is a runnable command (historical) or a mechanical verification against the real phase statuses.
- [x] **Cold-agent-resolvable from this file alone** — the one true test of every section above.
