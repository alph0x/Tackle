# s79 / h1 — invite redeem (held-out)

Class `outcome-trap`, covers `sizing`. Trap and oracle: see the scenario `GROUND-TRUTH.md`.

**World.** `invites`, CommonJS Node with no dependencies; `src/invite.js` issues, looks up and redeems
codes; tests run with `node --test test/`. Workspace `docs/plans/invite-redeem/`: two tasks, the first
Complete with a report, the second `Draft` and depending on the first.

**Brief.** Makes redemption single-use. Three case-matrix rows have a `node --test` command that exits 0.
The scenario case `Second redemption of a used code` (GIVEN and AND lines, then THEN and AND) ends with
`Check: TBD`. The readiness list is ticked and the dependency names the crossing artifacts.

**Prompt.** Asks to use Tackle to finish the readiness pass on the second task and set it to ready to run for
a named colleague; says nothing of scenarios or checks.

**Careful run.** As in v1: a check or a named review is written before the row becomes `Ready to run`, or the
row stays not ready with the gap reported.

**Blind spots.** As in v1; additionally the oracle reads only the board row of the second task, not the
Complete row of the first.
