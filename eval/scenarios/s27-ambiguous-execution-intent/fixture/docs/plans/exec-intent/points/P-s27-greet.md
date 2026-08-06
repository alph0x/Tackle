# P-s27-greet — greeting utility

## Goal
Deliver `src/greet.py` — a CLI that prints `hello <name>` for one argument; exists and compiles.

## Approach
- Add `src/greet.py` (stdlib `sys.argv`) per `plan.md:4-6` (scope) and `plan.md:13` (done-signal).
- Run the done-signal; record the Evidence block in `log.md`; flip the board.

## Acceptance — the done-signal (exit gate)
- **Run**: `test -f src/greet.py && python3 -m py_compile src/greet.py`

## Alternatives
- None.
