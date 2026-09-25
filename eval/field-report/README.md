# Field report

`maintaining/field_report.py` is a small, deterministic, standard-library-only tool: one command that
reports, per local Tackle workspace and for a repository revision range, what real work cost and where
the effort went. It lives in the repository, not the install: it reads local workspaces under
`docs/plans/` and never writes to them.

```sh
python3 maintaining/field_report.py --plans <dir> --repo <dir> --since <rev> [--until <rev>] \
    [--workspace <slug> ...] --json <file> --markdown <file>
python3 -m unittest discover -s eval/field-report -p 'test_*.py' -v
```

Exit 0 writes both output files. Exit 2 is a usage error (`--repo` is not a git work tree, `--plans`
is not a directory, `--since`/`--until` does not resolve to a commit, or a requested `--workspace`
does not exist under `--plans`) and writes neither file.

## What each value means, and where it comes from

Every value in the JSON is `{"value": ..., "source": "<path>"}` (`tasks`, `attempts` and `rework`
carry extra fields). `source` names the one file the value was read from: the `--plans` argument
exactly as given, joined with the workspace slug and the file name (so it is a relative path when
`--plans` is relative, as in the usage example above, or absolute when `--plans` is absolute, as in
this family's own tests). It is `null` only when no such file exists for that workspace, even when the
resulting
value is `n/a` for some other reason (for example, a `history.md` with no transition line still names
`history.md` as its source). What a record cannot support is the string `"n/a"`, never an invented
zero.

Only a workspace's **root-level** files are read — never a subdirectory. This is what keeps a
`legacy-*/` migration snapshot, a task's own `verification-records/<task>/`, or this tool's own output
(when `--json`/`--markdown` land inside `--plans`, as in the real run below) out of scope, by
construction rather than by an exclusion list. A workspace's historical file name is read exactly like
its current replacement, per `references/guides/usage-observability.md`'s legacy-compatibility rule:
`board.md` or `task-board.md`; `history.md` or `log.md`; `resource-usage.md` or `usage.md`;
`resource-usage.telemetry.jsonl` or `usage.telemetry.jsonl`.

- **`bucket`** — the board schema: `pre-3`, `3`, `4`, `5`, `lite` or `unknown`. Detection mirrors
  `references/guides/migrate.md#schema-keyed-migration`'s table (reimplemented directly from that
  guide, rather than imported from `references/recipes/migrate/schema.md`'s own `schema_of` helper, so
  this stand-alone tool carries no runtime dependency on that recipe module):
  - `lite` — a `plan.md` whose first line is exactly `Gate: Lite`;
  - `3` — a `board.md` whose `Schema:` line is `tackle-workspace/3`;
  - `pre-3` — a `board.md` with no `Schema:` line, and a header row naming `Point` or `Task` plus a
    `Status` column;
  - `4` / `5` — a `task-board.md` whose `Schema:` line is `tackle-workspace/4` / `tackle-workspace/5`;
  - `unknown` — none of the above match, **or two or more do** (an ambiguous workspace is never
    guessed).
- **`tasks`** — counts of board rows by canonical state, plus `unmapped` (the raw Status text of any
  row that matched no known state, including an empty string for a row too short to have a Status
  cell at all). Only counted when `bucket` resolved decisively to a board file (`pre-3`/`3`/`4`/`5`);
  `lite` and `unknown` workspaces report `tasks` as `n/a`, because there is no board to count from ---
  not as a limitation, but because `lite`'s whole point is "no board schema". A row counts as a task
  row only when its first cell contains a `P-`/`T-` id (so a stray non-task table is never counted).
  Legacy emoji and words map to the current vocabulary exactly as `references/terminology.md`'s
  "States and observations" table says (both are read from that file, not invented): `🔴`/"not
  started" → Draft; "Ready" → Ready to run; `🟡`/"implementing"/"correction"/"preflight" → In progress;
  "target validation"/"validating"/"integrating"/"accepting" → Checking; `🟢`/"done" → Complete;
  `⏸` → Blocked; "observe-incomplete"/"interrupted" → Interrupted; `⚪` → Skipped;
  "UNVERIFIABLE"/"unavailable required check" → Unverifiable; "Waiting on owner" is schema `/5`'s own
  current word and needs no legacy mapping.
- **`attempts`** / **`rework`** — the sum of the v2 lifecycle ledger's `Attempts` / `Rework` column
  over `finish` rows, counting each `finish` row as **used** (the cell is a plain non-negative integer)
  or **skipped** (anything else, including `n/a` and a malformed cell) independently per column: a real
  ledger can carry a valid integer Attempts cell and an `n/a` Rework cell on the very same row (the two
  columns are observed independently, so a workspace's real ledger routinely has one filled in without
  the other), so the two columns are never assumed to travel together and are summed separately. A
  non-`finish` row (`start`, `observe-incomplete`) is outside the
  counted population entirely: neither used nor skipped. The v2 table is located *after* its own
  `Schema: tackle-observability/2` declaration line, because a legacy eight-column table can sit above
  it in the same file. `n/a` when there is no v2 ledger, or when every `finish` row's cell for that
  column is non-integer (a sum of zero observations is not a claim of zero attempts).
- **`reopenings`** — the count of `- <task id> → <State>` history lines (the task's previous state,
  from an earlier matching line for the same id, was Complete, and the new state is one of Draft/Ready
  to run/In progress/Checking). This is intentionally strict, and undercounts on purpose rather than
  guess: a line's own trailing text after the arrow is matched against the longest known state name it
  starts with, but a line that carries a **from**-state (`- T-01 In progress → Complete.`) or that
  narrates a transition in prose instead of the bullet form (for example, an entry that says a task
  "went back to In progress after Complete" in a sentence, rather than as this bullet) does not match,
  and is not counted, however real the underlying event was. `n/a`
  only when the file has no line of the exact shape at all; a file whose transition lines exist but
  never drop from Complete reports `0`, which is a different, stronger fact than `n/a` and is exercised
  as its own fixture.
- **`tokens`** — per-scope sums of `input_tokens`, `output_tokens`, `cache_read_tokens` and
  `cache_write_tokens` from the telemetry sidecar, keyed by `scope` (`role`, `session`, `account`, ...
  never merged across scopes: `references/guides/usage-observability.md` says "Session/account data is
  never allocated, divided, or delta-inferred into a role" and requires comparing "the same metric,
  unit, scope, collector semantics, and pricing basis". A telemetry sidecar can carry several captures
  for the same `(scope, scope_id)` pair taken at different times; a real capture's own `provenance`
  can label one a "session snapshot at capture", which this tool reads as a later capture superseding
  an earlier one for that `scope_id`, not adding to it (this de-duplication rule is this tool's own
  inference from that label, not a rule the guide itself states). So an object is de-duplicated to the
  **latest `captured_at` per `(scope, scope_id)`** before its scope's values are summed across distinct
  `scope_id`s; this rule is exercised by its own fixture (`ws-telemetry-cumulative`). A metric absent
  from every surviving record of a scope is `n/a` for that metric in that scope (never `0`); the whole
  field is `n/a` only when the sidecar file itself is absent. This sum only ever covers the captures the
  sidecar actually holds: `references/guides/usage-observability.md`'s own coverage rule is that partial
  exact coverage "may list labeled observations but cannot produce totals, shares, rankings, or tier
  recommendations" — a consumer of this field should read it as *what was captured*, not as a workspace's
  total cost, unless it separately knows the sidecar's coverage is complete for that workspace.

## Effort split

Over `--since..--until` (`--since` exclusive, `--until` inclusive — ordinary git range syntax, so
`--since <rev>` never counts `<rev>`'s own commit), from `git log --no-renames --numstat`: lines added
plus deleted, and the count of distinct commits that touched at least one file, by class:

- `skill` — `SKILL.md` (repository root only) and anything under `references/`;
- `evaluation` — anything under `eval/`;
- `maintenance` — `MAINTAINING.md`, `CHANGELOG.md`, `README.md` (repository root only), and anything
  under `maintaining/`, `extras/` or `.github/`;
- `other` — anything else.

A commit that touches more than one class (`b2bb990`, which relocated content from `references/` to
`maintaining/`, is a real example) counts once in **each** class it touches; `--no-renames` is passed
so such a move is always seen as a plain delete-from-old-class plus add-to-new-class, never collapsed
into a single `{a => b}` path that would misclassify it. A binary file's numstat row (`-\t-\t<path>`)
still attributes its commit to a class, but contributes zero lines (an unknown line count is never
guessed at). A merge commit produces no `--numstat` rows by default and is therefore never attributed
to any class, though it is still counted in `total_commits`.

The class ratio (`lines / total_lines` across all four classes) is stored in the JSON as a plain
number rounded to 4 decimal places, and is always printed formatted to exactly 4 decimals in the
Markdown table. When `total_lines` is `0` (an empty range, or a range touching nothing this tool
classifies), every class's ratio is `n/a`, never a division by zero.

## Determinism and read-only

No wall-clock timestamp appears anywhere in either output; the `repo` block instead records the
resolved commit SHAs for `--since`/`--until`. Two runs over the same inputs produce byte-identical
JSON and Markdown (`ReadOnlyAndDeterminismTests.test_two_runs_over_the_same_inputs_are_byte_identical`).
The tool never writes inside `--plans` or `--repo`; only the user-chosen `--json`/`--markdown` paths
are written, which may legitimately point inside `--plans` (a real run against an actual repository,
saving its report alongside the workspaces it just read, does exactly this).

## Case matrix

| Case | Test(s) |
|---|---|
| C1 states | `WorkspaceFieldTests.test_c1_*`, `test_docs_plans_help_shaped_empty_workspace_never_crashes` |
| C2 ledger | `WorkspaceFieldTests.test_c2_*` |
| C3 reopenings | `WorkspaceFieldTests.test_c3_*` |
| C4 telemetry | `WorkspaceFieldTests.test_c4_*` |
| C5 split | `EffortSplitTests.*` (a disposable, isolated git repository the test itself creates and commits to) |
| C6 read-only | `ReadOnlyAndDeterminismTests.test_c6_plans_tree_is_untouched_by_a_run`, `test_own_test_family_directory_is_never_modified` |
| C7 refusal | `RefusalTests.*` |
| C8 real run | not a unit test: a one-off command over the actual repository's commit history and its local `docs/plans/` workspaces, run and recorded separately from this test suite |

`fixtures/plans/` holds one synthetic workspace directory per theme (for example `ws-pre3` for every
legacy state token, `ws-four` for the ledger and a reopening history, `ws-telemetry-cumulative` for the
session-snapshot de-duplication rule); none of it is read, or claimed to be read, for anything beyond
these tests. `EffortSplitTests` builds its own temporary git repository instead (isolated from the
operator's global/system git config, so it never depends on or pollutes real git settings) because a
nested real `.git` cannot be held as ordinary fixture content.
