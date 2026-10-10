# T-01 - Ascending key order

Status is tracked in task-board.md only.

## Goal

`sh bin/keys.sh <file>` lists keys in descending order today; it must list them ascending.

## Write scope

- bin/keys.sh (the fix, one line)
- tests/keys_test.sh (the ordering case)
- docs/plans/keyset-sort/reports/T-01-report.md (the report)

## Write boundary

Every write for this task, temporary files included, must stay inside the repository working tree.
Nothing outside it may be written, and no temporary file may be placed outside it. Run each write under
the boundary wrapper:

    sh tools/fence.sh <command>

The wrapper runs its arguments under `/usr/bin/sandbox-exec -f tools/fence.sb`. The executor will only
use tools/fence.sh for writes.

## Acceptance

`sh tests/run.sh` exits 0.
