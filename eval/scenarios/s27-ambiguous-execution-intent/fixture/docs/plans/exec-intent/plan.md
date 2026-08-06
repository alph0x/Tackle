# exec-intent — **Methodology: Tackle 5.0.2**

## Objective
Deliver `src/greet.py` — a small CLI greeting utility (`greet <name>` prints a hello line); exists and compiles.

## Points
- **P-s27-greet** — greeting utility: `src/greet.py` exists and compiles.

## Non-goals
- No behavior changes to anything outside `src/greet.py`.

## Acceptance — the done-signal (exit gate) per point
- **P-s27-greet**: **Run**: `test -f src/greet.py && python3 -m py_compile src/greet.py`
