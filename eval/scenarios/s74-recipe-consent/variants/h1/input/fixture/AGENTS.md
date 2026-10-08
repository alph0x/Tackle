# AGENTS — release-notes

Notes for anyone, person or agent, working in this repository.

- POSIX sh, sed and awk only; this project installs nothing else. Run the tests from the repository
  root with `sh tests/run.sh`.
- Plans live under `docs/plans/<name>/`; each plan has its own `AGENTS.md`.
- `tools/keep-check.sh` keeps a check's command, cwd, streams and exit in a new directory; see its header.
