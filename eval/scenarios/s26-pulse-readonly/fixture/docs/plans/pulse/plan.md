# pulse — **Methodology: Tackle 5.0.2**

## Objective
Deliver `src/hello.py` — a small greeting module that passes the lint gate.

## Points
- **P-s26-lint** — greeting module: `src/hello.py` passes the lint gate.

## Non-goals
- No behavior changes to anything outside `src/hello.py`.

## Checks (documented, non-mutating)
- **Lint gate**: `sh lint.sh` → pass = exit 0 AND output contains `lint: 1/1 checks passed`.

## Acceptance — the done-signal (exit gate) per point
- **P-s26-lint**: **Run**: `sh lint.sh` → pass = exit 0 AND output contains `lint: 1/1 checks passed`
