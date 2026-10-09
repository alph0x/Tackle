# AGENTS — parcel-zones

Notes for anyone, person or agent, working in this repository.

- POSIX sh and awk only; there is no other runtime here. Run the tests from the repository root with
  `sh tests/run.sh`.
- Plans live under `docs/plans/<name>/`; each plan has its own `AGENTS.md`.
- `vendor/` holds third-party kits, copied in as each release ships.
- Keep `bin/supplement.sh` output a bare integer in cents: the dispatch desk pastes it into its labels.
