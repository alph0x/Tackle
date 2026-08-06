# tracker — **Methodology: Tackle 5.0.0**

## Objective
A tiny command-line plan tracker: add and list plan points from the terminal.

## Points
- **P-tracker-core** — `add`/`list` commands in `src/planner.py`.
- **P-tracker-storage** — points persist in `notes.txt`.

## Non-goals
- No sync, no accounts, no web UI.

## Acceptance — the done-signal (exit gate) per point
- **P-tracker-core**: **Run**: `python3 -m py_compile src/planner.py`
- **P-tracker-storage**: **Run**: `test -f src/notes.txt`
