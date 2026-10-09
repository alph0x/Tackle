# AGENTS — shelf-labels

Notes for anyone, person or agent, working in this repository.

- The tool and its tests are POSIX sh and awk. Run the tests from the repository root with
  `sh tests/run.sh`.
- Plans live under `docs/plans/<name>/`; each plan has its own `AGENTS.md`.
- `build/` holds rendered label files; the print shop takes them byte for byte, so keep each label
  block exactly as specified (call number line, title line or lines, one blank line).
