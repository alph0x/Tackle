# flip-gate — **Methodology: Tackle 5.0.0**

## Objective
Deliver a compilable `src/flip.py` flip module for the gate demo.

## Points
- **P-s23-flip** — flip module: `src/flip.py` exists and compiles.

## Non-goals
- No behavior changes to anything outside `src/flip.py`.

## Acceptance — the done-signal (exit gate) per point
- **P-s23-flip**: **Run**: `test -f src/flip.py && python3 -m py_compile src/flip.py`
