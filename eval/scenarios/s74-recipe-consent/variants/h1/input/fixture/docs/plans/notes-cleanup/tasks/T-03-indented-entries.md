# T-03 — Indented entries

- **Goal**: `bin/notes.sh` treats an entry indented with spaces or tabs (`  fix: text`) like any other
  entry (`- **fix**: text`); lines that are not entries still print nothing.
- **Inputs**: `bin/notes.sh:4`; `tests/bullet_test.sh`; `tests/type_test.sh`; D-01; D-02.
- **Write scope**: `bin/notes.sh`; a new `tests/indent_test.sh`; this workspace's board, history, resource
  usage, `reports/T-03-report.md` and `verification-records/T-03/`.
- **Non-goals**: the existing tests, `tests/run.sh`, `tools/`.
- **Acceptance**: `sh tests/run.sh` exits 0, and `tests/indent_test.sh` feeds a space-indented entry, a
  tab-indented entry and a `#` line and asserts exactly the two bullets, in order.
- **Verification record** (D-01, D-02): under `verification-records/T-03/`, the exact command, cwd,
  complete stdout and stderr and exit status of the acceptance run, and copies of `bin/notes.sh` and
  `tests/*.sh` as they were at the run. The report links the record.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
