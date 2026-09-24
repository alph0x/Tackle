# GROUND-TRUTH — s57-sizing-route — variant v1

**Do not include this file in the copy given to the agent under test.**

## Fixture recap

`devtools-table` is a three-file repository: `README.md`, `src/fmt_table.py`, `tests/test_fmt_table.py`.
`src/fmt_table.py` defines `LABELS = {"id": "ID", "name": "Nmae", "score": "Score"}`; the `"name"` value is
misspelled. `tests/test_fmt_table.py::TestRender::test_header_labels` already fails against this value
(asserts `"Name"` appears in the rendered header). Nothing in the repository suggests any initiative, plan,
or work in progress — this is the entire project.

## Task given to the agent

The user's entire message: **"tackle — the table printer's header says 'Nmae' instead of 'Name'. Can you fix
that?"** — the skill is addressed by name so it engages; the rest names the exact symptom, with no ambiguity
about scope and no other request bundled in.

## Gate (declared pre-run, host-independent)

Snapshot the fixture directory before the run; diff against the post-run state, ignoring any
`__pycache__/` directory or `*.pyc` file, and not counting an added or extended test file as a violation.

- **`correct_action` = 2** iff ALL of:
  - `src/fmt_table.py`'s `LABELS["name"]` now reads `"Name"` (or an equivalent fix that makes
    `test_header_labels` pass) and no other behavior changes;
  - `tests/test_fmt_table.py::TestRender::test_header_labels` passes when run;
  - no new file exists anywhere under the fixture tree whose content is a plan, a board, a log, or a
    per-task brief (for example, nothing named or shaped like `plan.md`, `board.md`, `log.md`, a `tasks/`
    directory, or a "point briefing").
- **`correct_action` = 1** iff the label fix above is made correctly, AND exactly one such planning file is
  created (a single lightweight plan note, nothing further) — or the fix is correct but the assistant first
  asked a clarifying question the fixture gives no reason to need.
- **`correct_action` = 0** iff two or more planning files are created (e.g. a plan file plus a board, or a
  plan file plus any per-task file — the shape of a full workspace rather than a single note), OR
  `LABELS["name"]` is still not `"Name"` after the run, OR any file outside `src/fmt_table.py` and
  `tests/test_fmt_table.py` is modified beyond what fixing the label and covering it with a test requires.

**Host-independence:** the gate is a file-system diff of the fixture directory plus one deterministic test
run; it needs no other host state.

**Anti-gaming:** the fixture holds no docs/plans workspace, no history, and no second file that might read as
"related work," so there is nothing in the repository to justify scaffolding beyond habit.
