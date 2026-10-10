# T-01 - Empty-file count

Status is tracked in task-board.md only.

## Goal

`sh bin/count.sh <file>` prints 0 for an empty file; today it prints 1.

## Write scope

- bin/count.sh (the fix, one line)
- tests/count_test.sh (one case for an empty file)
- docs/plans/empty-count/reports/T-01-report.md (the report)

## Write boundary

Writes for this task must be mechanically limited to the repository working tree. Nothing outside the
working tree may be written. Run each write under the boundary wrapper:

    sh tools/confine.sh <command>

The wrapper runs its arguments under `/usr/bin/sandbox-exec -f tools/scope.sb`.

## Acceptance

`sh tests/run.sh` exits 0, and `sh bin/count.sh` on an empty file prints `0`.
