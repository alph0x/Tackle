# Decisions

## D-01 — Check records

- Every acceptance run keeps a record under `verification-records/<task>/<run>/`: exact command, cwd,
  complete stdout and stderr, and exit status. 2026-10-04.
