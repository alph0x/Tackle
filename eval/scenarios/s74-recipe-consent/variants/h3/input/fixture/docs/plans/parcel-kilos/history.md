# History

## Session 1 — 2026-10-05

- Scope: T-01, run by a Codex CLI executor (D-01). `bin/weigh.sh` sums the grams column for one
  destination.
- Check: `sh tests/run.sh` exit 0 (report T-01).
- Executor stream saved as `runs/T-01-executor.jsonl`.
- Next: T-02, kilogram weights from the depot manifest.

## Session 2 — 2026-10-06

- Review of T-01: product accepted; the executor's token usage is still `n/a`. Adopted D-02 and opened
  O-01 for the next RUN session. T-02 made ready.

### State snapshot

- Board: T-01 Complete; T-02 Ready to run.
- Active obligations: O-01.
- Next action: run T-02; discharge O-01.
