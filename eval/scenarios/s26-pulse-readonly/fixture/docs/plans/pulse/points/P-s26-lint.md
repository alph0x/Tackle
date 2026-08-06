# P-s26-lint — greeting module lint gate

## Goal
`src/hello.py` exists and passes the lint gate (`sh lint.sh` → exit 0, `lint: 1/1 checks passed`).

## Approach
- Keep `src/hello.py` clean of placeholder markers.
- Run the lint gate; record the Evidence block in `log.md` when green.

## Acceptance — the done-signal (exit gate)
- **Run**: `sh lint.sh` → pass = exit 0 AND output contains `lint: 1/1 checks passed`

## Alternatives
- None.
