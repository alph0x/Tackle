<a id="full--executable-observations-and-bounded-closure"></a>
# Coordinated — verification records and bounded completion

Use an equivalent complete harness export when available. Otherwise, with the owner's explicit
authorization ([script consent](../../scripts/README.md#consent)), run the Python 3 [capture script](../../scripts/capture.py)
from an authorized cwd before running checks: an optional script, not an installed runner or a new
product dependency. This is Coordinated's direct-capture entry from `run.md` and `evidence-capture.md`;
Direct and Focused keep their own procedures.

## Establish the boundary first

Record allowed writes, protected fixtures and the actual harness policy. Configure native
filesystem restrictions for shell children as well as patch tools; a container protects its host,
not necessarily the task's Write scope inside the container. Put script revisions, evidence and
TMPDIR under authorized paths. TMPDIR routes cooperative tools; it does not prohibit an explicit
`/tmp/name`, a sibling path or a symlink escape.
Name the selected executor and every write channel it has: shell children, the host's own edit or
patch tool, and any tool that writes its own files. Report one line per channel above, marked confined (observed with
disposable sentinels through the task's mechanism), unavailable to that executor (shown
by its configuration, not by intent) or uncovered (unobserved or partly observed). An
unavailable channel needs no probe. A promise not to use an available channel enforces nothing.
Setup writes that prepare confinement (a profile, probe script or evidence) are
new coordinator files in authorized workspace paths, recorded as setup; never edit a supplied profile or launcher. Before the first
task-scope write, use disposable sentinels to prove an allowed write succeeds and outside/protected
writes are denied. Never probe by writing, replacing or deleting a real file. Preserve the observed
policy and results. A launcher that fails to start is a launch failure, not proof that confinement is
unavailable. The executor's own sandbox (e.g. Codex workspace-write) is a host mechanism: probe it
once within existing authorization before requesting an exception or requirement change. When every channel
is confined or unavailable, record the evidence and proceed without an exception. If effective
confinement is a required capability and a channel stays uncovered, block only the affected scope
and name the missing channel, operation or observation; do not claim that every alternative is
impossible, do not disable confinement, and do not claim that an instruction or audit enforces it. A
later successful probe never covers earlier writes; declare the gap. Post-run hashes remain
necessary for protected expectations.

## Prepare once, then capture

During PLAN, select a capture destination, exact command and input selectors for each obligation:
source, **all selected tests including additive files**, contract, input data, config and
dependencies. Selectors come from the acceptance/check's actual dependency surface, not merely
task Write scope. Review completeness before execution; no generic helper can infer every dynamic
input. A glob records its membership, including an intentionally optional empty match; a required
selector matching nothing is an error. Never select credentials, home directories or generated
evidence. Save compound scripts before invoking them and include every called script/config;
the script automatically includes itself (when it sits outside cwd the record names it in a `program` field with its absolute path and sha256 instead), its JSON specification and existing file arguments after argv[0]. The executable/runtime is
observed separately; absolute interpreter paths are valid. External read-only scripts need an
authorized local snapshot or equivalent harness capture; never widen write permissions to copy them.
A copied module loaded by an inline interpreter still needs its selector. Running the capture script
needs the owner's explicit authorization; an equivalent harness capture is preferred.

The script saves exact input bytes once per initiative in immutable content-addressed objects, with
compatible per-record blob aliases, binary streams and actual child status; it does not judge whether a
shell wrapper's logic is sound. Prefer direct runner argv; check each required child in compound scripts.
A printed PASS or a trailing successful command must never mask failure. A script correction gets a new
verification record; previous snapshots are never replaced. The script serves foreground children that
join their own children and cannot certify process-tree shutdown: on timeout, interrupt or background
work, use the harness to stop all writers and record that confirmation before closing evidence.

With the owner's explicit authorization, run [`scripts/capture.py`](../../scripts/capture.py) with one JSON specification path,
for example `python3 -I <skill>/scripts/capture.py docs/plans/demo/product-check.json`. The JSON has
`argv`, `selectors` (objects with `glob` and `required`), `artifacts` (relative file names),
`workspace` (the already authorized initiative directory) and `timeout_seconds`. Optional
`destination` must stay inside that workspace's `verification-records/` store; the default is the store itself.
Optional `prior_records` names exact prior record directories inside this same store, never a
glob. New specifications must declare workspace. Legacy specifications with only `destination`
still use that explicitly selected directory as their storage root; generate no new implicit
cwd destinations. See [record lifecycle](record-lifecycle.md) for retention/export and compatibility. Use an authorized absolute cwd as the
process cwd; paths resolve from it. For example selectors can cover `src/**/*.py`, `test*.py`,
`SPEC.md` and the exact validation/config files. Adapt to the real repository, not this example.

It prints the path of the new `receipt.md` and exits 0 when the check is accepted, 1 when it is not accepted
or when the specification is refused with a named `ValueError`; run it only with the owner's explicit
authorization for this use ([script consent](../../scripts/README.md#consent)).

Before reusing a verification record, reject any retirement tombstone, then open its result and verify stream/blob hashes, relevant final input
hashes **and selector membership**, produced artifacts and the actual successful child result.
Missing or altered bytes invalidate the record. `read_record` checks retained bytes and actual
child status for both old per-observation blobs and the shared layout; it never infers that
current source/configuration/runtime or semantic coverage is unchanged. A start without a complete result is
incomplete. Keep the old record and rerun only dependent checks. Hashes identify bytes; review of the
declared selectors establishes whether those bytes cover the obligation.

## Execute canonical lint faithfully

Run all 17 rows during PLAN before Ready with [`scripts/lint.py`](../../scripts/lint.py), which an
explicit plan or run request authorizes ([script consent](../../scripts/README.md#consent)):
`python3 -I <skill>/scripts/lint.py <slug>` from the repository root runs rows 1-17 in order, and
`--row N` runs one row, passing its stdout, stderr and exit through unchanged. Each row's program is
that file's `ROW_NN` constant with only a validated single-component slug (`[a-z0-9][a-z0-9.-]*`)
substituted for `<slug>`. For a captured record, save the canonical source snapshot/hash,
row number, command bytes and pass condition. Reject missing/duplicate rows, malformed row constants and
an unexpected source revision. Establish the expected hash from a reviewed, trusted skill revision
before reading workspace-provided input; a hash copied from the same unreviewed file proves only
byte consistency, not authority. Review any change to a row program before updating
that trust anchor. Never invent an equivalent short validator, replace a row with
`true`, or paste the programs into an interpolated shell string. Execute each saved command using
`['sh', saved_script]`; retain a separate raw check record for each row. The snapshot of the saved
script must match the extracted bytes. A script's trailing `printf` cannot supply the row result.
Apply the same reviewed-revision rule to the configured capture script and its imports before
running the Python script; it is executable code with the caller's filesystem permissions.

For an existing orchestrator, the two pure Python functions `canonical_rows` and `lint_verdict` of
[`scripts/lint_runner.py`](../../scripts/lint_runner.py) provide exact extraction and row
interpretation. Save the extracted UTF-8 bytes verbatim as each script; capture that saved script
with the capture script above. Supply the canonical source hash recorded at preflight, not a hash silently
recomputed after a change. Check that all 17 returned rows are scheduled before initial execution.
Each result carries `row`, `command_sha256`, `source_sha256`, raw check record path and verdict;
build the index from those records. Equivalent harness automation is valid. Importing or running
these functions needs the owner's explicit authorization.

When equivalent harness automation is absent, the connected path below needs the owner's explicit
authorization; with it, run `python3 -I <skill>/scripts/lint_runner.py <lint.json>` from an authorized cwd.
It uses the `capture.py` beside it.
The runner reads the `lint.py` beside it, pinned by sha256 like `capture.py`. The JSON specifies `slug`,
`selectors`, `workspace` and `timeout_seconds`; a configuration naming `source` or `source_sha256` is refused. The capture script is pinned by the lint script by
sha256; only final newlines may vary, and any other bytes stop the run with `capture script revision
changed`. An optional `capture_script` names a copy of it inside cwd, held to the same pin. Review both
scripts before changing that pin. The workspace must already exist. Legacy `destination`-only
configurations are still accepted as an explicit workspace location; newly generated
configurations name workspace. Optional `rows` selects
affected checks; omission runs all 17. Initial PLAN still requires all 17. Include citation targets
and other actual dependencies in selectors. Helpers and outputs stay inside cwd. The script extracts, saves, captures and verifies
each command itself; never transcribe row programs by hand into another script. A custom
composition stays possible, but compare its actual captured script bytes with the extracted
canonical bytes before claiming canonical coverage. A source/command mismatch or absent script
snapshot is ERROR even if the command exited zero. A subset score is never a full-plan approval.

The runner (outside cwd, it lists itself and the capture script under `programs` in the summary) prints the path of the batch's `summary.json` and exits 0 when every selected row's verdict is PASS or
WARN, 1 otherwise; a refused configuration ends with a named `ValueError`, and the runner runs only with the
owner's explicit authorization for this use ([script consent](../../scripts/README.md#consent)).

Interpret **stdout, stderr and real exit together** using the canonical condition:

| Rows | Empty-output pass | Findings | Execution error |
|---|---|---|---|
| 5 | stdout/stderr empty, exit 1 | stdout with grep exit 0: FAIL | stderr, timeout, signal or other exit: ERROR |
| 15 | stdout/stderr empty, exit 0 or 1 | stdout: WARN if exit 0 or 1 and no stderr | stderr, timeout, signal or other exit: ERROR |
| 8, 13 | stdout/stderr empty, exit 0 | stdout with exit 0: WARN | stderr, timeout, signal or nonzero exit: ERROR |
| 6, 11, 16 | stdout/stderr empty, exit 0 | stdout with exit 0 or 1: FAIL | stderr, timeout, signal, unexpected exit or empty-output exit 1: ERROR |
| All other rows | stdout/stderr empty, exit 0 | stdout with exit 0: FAIL | stderr, timeout, signal or nonzero exit: ERROR |

Row 17 belongs to the last line: its findings print with exit 0 (FAIL), and its structural refusals, `migrate first` and a missing `history.md`, exit 1 (ERROR).

Report every finding verbatim, including findings printed with exit zero. WARN keeps its existing
nonblocking severity; ERROR means the row was not validly observed, never PASS. Preserve failures;
wrapper success never certifies them. The capture script's `accepted` means a captured zero exit with stable inputs and present
required artifacts; lint's row-specific verdict uses its captured fields, not that generic boolean.
The score is computed from these records, never a constant or a count of launched commands.

## Close against one obligation index

Before RUN, prepare the obligation → command → input selectors → evidence destination mapping,
including required reviews, runtimes, integration/global coverage and packaging. Reuse PLAN's
preparation and canonical lint records after checking their revisions. After product checks,
write the reports, board/log/usage updates and final output references once, then validate their
affected rows. Link a captured verification record from the ledger/report instead of transcribing it.
A verification record may satisfy several obligations when its actual coverage does; never rerun a
passing product suite merely to fill separate target, integration and global headings.

Use this dependency map conservatively when selecting affected lint rows:

| Changed input | Invalidated rows |
|---|---|
| Workspace top-level or one-level Markdown content/membership | 1 |
| Task briefs or plan, including id/dependency membership | 2, 5; task briefs also 7, 9, 12 |
| Task board (`task-board.md`) | 2, 3, 10, 11, 14, 17; every initiative board also 8 |
| Task brief/plan/reference citations or their target bytes | 4 |
| History (`history.md` or `history-archive.md`) content/membership | 6; active history also 13 and 17 |
| Design contract or decisions | 7 |
| Any initiative's task brief/Write scope membership or content | 8 |
| Resource usage (`resource-usage.md`) membership/content | 11, 16 |
| Closure report membership | 14, 17 |
| A Complete task's report content (its `**Remains**:` line) | 17 |
| Workspace AGENTS | 13, 15 |
| Reference-doc membership/content, current time crossing freshness window | 15 |
| Lint source, command interpreter/tools or policy relevant to its execution | All affected rows; all 17 if impact cannot be established |

Union dependencies; one edit can match several rows. Track glob membership, citation target files
and time as well as hashes of known files. Never reuse row 15 without a verified expiry boundary;
rerun this inexpensive row when freshness is uncertain. Unknown dependencies invalidate the
potentially affected records. Product checks have their own input map.

The final index still accounts for all 17 canonical rows, distinguishing fresh executions from
reused current records; report `lint: N/17 checks passed` from their actual pass conditions
(and any additional workspace rows in the denominator). This is a current coverage summary;
also report how many rows were executed versus reused. A selection of custom checks is not 17/17.
The release sweep still executes every prescribed row and gate; this reuse rule does not waive it.

Finish with complete only when all mandatory obligations have current accessible evidence;
otherwise with the bounded blocker packet from `run.md`, preserving completed unaffected work and the
unresolved obligation. Budget exhaustion ends with an honest incomplete/blocked handoff, never
justifying changed acceptance, omitted global coverage or another unbounded bookkeeping loop.
Correct an observed failure within the existing recovery budget; never restart unchanged preparation
merely because a new heading or session begins.

Explicit Focused applicability uses the first-line marker and shape checks in `lint-spec.md`, not
absence of Coordinated files. Include plan.md in selectors for every row: route changes invalidate all
applicability records. During release, execute all seventeen commands even for Focused and accept
Coordinated-only checked skips only after row 1 passes. This does not waive selected global acceptance.
