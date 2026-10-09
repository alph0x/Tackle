# AGENTS — parcel-cover

Notes for anyone, person or agent, working in this repository.

- POSIX sh and awk only; there is no other runtime here. Run the tests from the repository root with
  `sh tests/run.sh`.
- Plans live under `docs/plans/<name>/`; each plan has its own `AGENTS.md`.
- Keep `bin/premium.sh` output a bare integer in cents: the parcel desk pastes it into the booking form.
