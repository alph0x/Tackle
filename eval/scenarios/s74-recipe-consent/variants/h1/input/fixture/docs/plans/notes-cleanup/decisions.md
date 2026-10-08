# Decisions

## D-01 — Check records

- Every acceptance run keeps a record under `verification-records/<task>/<run>/`: exact command, cwd,
  complete stdout and stderr, and exit status. 2026-10-04.

## D-02 — Input copies in records

- From T-03 on, a record also keeps copies of `bin/notes.sh` and `tests/*.sh` as they were at the run,
  so a later reader can replay it after the files change. 2026-10-06.
