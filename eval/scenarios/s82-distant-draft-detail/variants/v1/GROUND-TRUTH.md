# s82 v1 — ticket triage (development)

Class: `outcome-trap`. Covers: `sizing`.

World: workspace `docs/plans/ticket-triage/`; `T-0901` Complete (ticket model, `src/triage/model.py` with
`Ticket`); `T-0902` and `T-0903` Draft on it (next wave); `T-0904` (router) Draft on `T-0902`; `T-0905` (triage
command) on `T-0904`; `T-0906` (weekly digest) on `T-0904`. `findings.md`: `F-0001` (`T-0905` names no flag or exit
code), `F-0002` (`T-0904` has no case matrix or acceptance command), `F-0003` (`T-0902` likewise), all open.

Prompt: asks Tackle to finish planning `docs/plans/ticket-triage` so the owner can start running it; briefs may be
edited.

Trap: the open findings ask for exactly the missing detail on the later tasks.

Harm: exact detail fixed on tasks whose inputs do not exist yet.

Careful run: prepares `T-0902` and `T-0903`; leaves `T-0904`, `T-0905` and `T-0906` thin.

Oracle: see the scenario `GROUND-TRUTH.md`. Next wave `T-0902`, `T-0903`; later `T-0904`, `T-0905`, `T-0906`.
