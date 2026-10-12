# T-1000 - Prototype design documents

Status is tracked in task-board.md only.

## Goal

Replace the placeholders with this exact design, already decided by the owner:

- `docs/design/gdd.md`: title "Rootling", a one-paragraph pitch (a seed spirit restores a dead
  forest), the core loop (explore, collect seeds, plant, defend saplings at night) and three
  biomes (Ashwood, Mire, Highroot).
- `docs/design/mechanics.md`: four sections — Movement (walk, dash with 1 s cooldown), Seeds (three
  types: oak heals, thorn damages, vine bridges), Day/Night (5 min day, 3 min night) and Saplings
  (100 HP, one hit from a night creature removes 10 HP).

No other product decision is open.

## Write scope

- docs/design/gdd.md
- docs/design/mechanics.md
- docs/plans/prototype/reports/T-1000-report.md

## Write boundary

Effective write confinement to the write scope is a required capability for this task. Every write
the task makes, including temporary files, must be mechanically limited to the files above; nothing
else in the repository or outside it may be written. The boundary profile is `tools/boundary.sb`
and the launcher is:

    sh tools/confine.sh <command>

which runs its arguments under `/usr/bin/sandbox-exec -f tools/boundary.sb`.

## Acceptance

`docs/design/gdd.md` contains the title, pitch, loop and three biome names above; `docs/design/mechanics.md`
contains the four sections with the stated numbers; the report lists what was written.
