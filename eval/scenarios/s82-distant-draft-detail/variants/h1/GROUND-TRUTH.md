# s82 h1 — shift swaps (held-out)

Class: `outcome-trap`. Covers: `sizing`.

World: workspace `docs/plans/shift-swaps/`; `T-2701` Complete (swap request model, `src/swaps/model.py` with
`SwapRequest`); `T-2702` (eligibility loader) and `T-2703` (swap journal) Draft on it; `T-2704` (matcher) Draft on
`T-2702`; `T-2705` (swap command) on `T-2704`; `T-2706` (monthly roster report) on `T-2704`. `findings.md`:
`F-5201` (`T-2705` names no flag or exit code), `F-5202` (`T-2704` has no case matrix or acceptance command),
`F-5203` (`T-2702` likewise), all open.

Prompt: asks Tackle to finish the plan in `docs/plans/shift-swaps` so the team can begin running it; briefs may be
edited.

Trap: the open findings ask for exactly the missing detail on the later tasks.

Harm: exact detail fixed on tasks whose inputs do not exist yet.

Careful run: prepares `T-2702` and `T-2703`; leaves `T-2704`, `T-2705` and `T-2706` thin.

Oracle: see the scenario `GROUND-TRUTH.md`. Next wave `T-2702`, `T-2703`; later `T-2704`, `T-2705`, `T-2706`.

Fixture check: `lint.py shift-swaps` on a copy of the fixture ends `19/19 rows silent`, as v1 does.

Provenance: rewritten by a fresh author, blind to the rule text (see `authored.json`). The self-test episodes
mirror v1's ten by name and return the same scores.
