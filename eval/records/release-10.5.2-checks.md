# Tackle 10.5.2 checks and evidence limits

This report describes the checks behind the 10.5.2 release notes. Final candidate registries, install inventories, local CI replay and publication observations are separate release gates. No held-out behavioral result is claimed.

## Migration vocabulary

The migration diagnosis validated every task board against the vocabulary of the older schemas, which lacks `Waiting on owner`. A schema-5 board holding that state was diagnosed as unknown, and the same board with `Blocked` instead was diagnosed as started.

Two end-to-end tests now run the installed migration command line. The first reads the state list from the installed board template, requires it to match the expected classification of each state, and diagnoses a board with each listed state; it also checks that an unlisted status and a legacy status glyph give unknown on a schema-5 board, that `Waiting on owner` on a schema-4 board still gives unknown, and that two diagnoses of the same input give identical manifests. The second migrates a board whose task waits on its owner with an empty next wave, and checks that the waiting row, its reference and the referenced question survive adoption byte for byte; with the dependent task as the next wave, verification fails with the dependency finding and the source stays unchanged; with the waiting task as the next wave, the diagnosis refuses it.

Both tests failed before the change on Python 3.10.7 and on the 3.10.22 floor, and the whole migration test file passed after it on both. Seven planted faults each failed at least one test: widening the shared vocabulary, accepting any status, classifying the waiting state as ready work, rewriting the waiting row inside the migration, dropping the dependency finding, admitting the waiting task to the next wave and applying the new vocabulary to older schemas. The schema adapters for older boards are unchanged and still pinned by hash.

## Orphan terminal repair

A ledger run whose only row is a terminal failed lint row 16, and the record writer could not repair it: it refused a start once a terminal existed and only appended at the end of the table. The new `reconcile` kind inserts the start immediately before the terminal. It reads the ledger rows as row 16 does, so a row separated from the table header by blank lines or notes is found too; the first version read only the rows directly under the header and refused the orphans of a real ledger written in several blocks, which was found while migrating that workspace with the candidate and corrected before release.

Three tests run the writer's command line. The first repairs an orphan `finish` and an orphan `observe-incomplete` next to a normal pair and two rows with irregular spacing, and compares the exact ledger and history bytes: each start sits right before its terminal, every other row is unchanged, the history holds the two events, no telemetry file is written, and row 16 fails before and passes after. The second checks that an unknown run, a run with a start, a run with two rows, a start-only run, a duplicate event id, an empty, multi-line or missing observation, a ledger without its schema marker, a legacy table and a second table header are refused without any write. The third splits the ledger into three blocks separated by a blank line and a note, repairs orphans in the second and third blocks, one of them with an empty last cell, compares the exact bytes, and checks that two runs whose start and finish sit in different blocks are refused without any write.

The first and third tests failed before their changes on both interpreters, and the record-tool tests passed after them on both. Nine planted faults each failed a test: appending the start at the end, accepting a run that already has a start, copying the terminal's clock, skipping the history event, rewriting every row, accepting a second table header, reading only the first block, reading only the terminal's block and counting cells in a way that drops an empty last cell.

## Diagnosis preflight

The `diagnose` command wrote only the manifest, so lint findings that would hold verification appeared only after the copy was prepared. It now runs lint rows 1 to 19 on an isolated temporary copy of the workspace and writes the verdicts beside the manifest.

One end-to-end test diagnoses a clean workspace, a workspace with an orphan terminal, a workspace with a neighbor that would change row 8 on the live tree, an older-structure workspace, a workspace holding a read-only directory and a run whose sidecar already exists. It checks that every verdict matches the verdict function recomputed from the recorded output, that the orphan terminal fails row 16 and the summary names the repair, that the neighbor does not change the isolated verdict, that the older structure is skipped, that the read-only directory does not stop the cleanup, that an existing sidecar is refused before the manifest is written, that the exit code stays 0 and the manifest keeps its keys, and that the source and the temporary directory are left as they were.

The test failed before the change on both interpreters, and the migration test file passed after it on both. Eight planted faults each failed it: writing the sidecar inside the workspace, taking the verdict from the exit code only, exiting 1 on findings, adding a manifest key, running lint on the live tree, running lint for an older structure, leaving the temporary copy behind and removing it without restoring write permission. An independent review found the read-only directory case before the change was accepted; the correction and its test were added then.

## Cited project files

The diagnosis preflight and the verification captures lint an isolated copy that held only the workspace folder, so a citation of a project file outside `docs/plans/` read as stale there while it passed on the real tree, and verification could not pass for such a workspace. This was found while migrating a real workspace with the candidate and corrected before release. Each isolated copy now also holds the cited project files with a plain relative path, recorded with their hashes; verification rechecks every recorded copy whenever it runs, including on a resumed or already verified job.

One end-to-end test diagnoses, prepares and verifies a workspace whose plan and task brief cite a project document: the preflight and all four captures record exactly that file and pass the citation row. It checks that a citation into another workspace, through a symbolic-link directory or with a parent segment is not copied, that a pre-existing different file at the copy path is refused, and that a changed copy is refused in the candidate copy, in the diagnostic copy and after verification succeeded. The test failed before the change on both interpreters, and the migration test file passed after it on both. Seven planted faults each failed it: copying only in the preflight, copying files under `docs/plans/`, following a symbolic link, accepting every recorded entry, not recording the copies, skipping the recheck at verification and overwriting a different existing file.

## Snapshot and freeze

Stamp preconditions run before the pre-stamp capture. The route requires a current candidate State snapshot and carries only the newest snapshot into the migration event. The guide states the first-verify freeze and the fresh-job iteration path. A changed source also requires a fresh diagnosis.

Target checks and independent review covered snapshot selection and refusal before capture or stamp effects. Existing schema adapters remained unchanged. These checks do not infer the truth of a free-form snapshot from a successful command.

## README carrier

README is an allowed candidate carrier. The final stamp updates its first existing methodology stamp. It does not invent a stamp in an unstamped README. Candidate read-list edits do not authorize source writes.

Installed-CLI checks and independent review covered the carrier and stamp behavior. The added behavioral rule has no dedicated held-out evidence cohort.

## Active decisions

Migration, the record writer and lint recognize the same active-decision heading. The decision ID ends at an ASCII space, tab or line end. A non-breaking space is not a boundary. The heading still requires the literal active marker.

The accepted corpus ran against all three consumers in the C and UTF-8 locales. Independent correction review checked the shared boundary and the restored reset in lint row 14. Every unrelated part of that row remained byte-identical to the base.

## Selection and lifecycle

Prepare registers source selection before its first state. It records source-shaped carriers, literal procedure revisions or null, source diagnostic limits and non-hidden neighbors. Source briefs without board rows retain their identities and procedure values. Neighbor changes hold verify and adopt; hidden entries stay excluded and links are not followed.

After stamping, verify retains the fixed installed lifecycle command, its full streams, status and bindings. Failed or malformed output holds admission. Coverage values never gate. Registered receipts remain immutable across cutover and terminal verify/adopt reuse.

The installed-CLI methods passed on the host and on the 3.10.22 floor. Planted faults were caught, including a hidden-only neighbor change. The final correction aligned source discovery with the existing heading and file-name conventions. Complete affected acceptance passed with 2472 tests. An independent correction review accepted the final bytes. Three earlier correction validations and one review hold are retained in the task records.

## Closed-task receipts

When the R family applies, diagnosis names each Complete task with a receipt gap. It names a missing report, a missing or invalid report baseline, and a missing, conflicting or duplicate first history line. It reads the archive before the active history and ignores fenced lines. It emits one row per task. Skipped and Unverifiable tasks are not named. Sources without gaps diagnose to the same manifest bytes as before.

For an unstamped source or one older than 10.2.0, verification holds while any such gap remains. The comparison is numeric, so 10.2 and 10.2.0 are not held. Migration never writes either receipt line.

Two installed-CLI methods failed before the change and passed after it on both runtimes. Seven planted faults each failed a named method. Complete affected acceptance passed with 2474 tests. An independent review ran the migration file and its own installed-CLI probe, and accepted the change.

## Lint row 8 temporary file

Row 8 lists the tree's symbolic links in a temporary file. It created that file with a bare `mktemp`, which on macOS writes under the per-user system directory even when `TMPDIR` is set. This was found while locking the real-workspace migration, whose scope confines every write. The row now creates the file under `TMPDIR`, or `/tmp` when it is unset, and still removes it.

Method A in the lint-row family runs the real row with a recording `mktemp` placed first on `PATH`. It failed before the change and passed after it on both runtimes. Three planted faults each failed it: the bare call, a template outside `TMPDIR` and a missing removal. An independent review found row 8's output identical to the base on sixteen fixtures. Complete affected acceptance passed with 2475 tests.

## Selected-checkpoint diagnostic

The family-P instruction asked for the current diagnostic under each task's pinned procedure. The installed route records only its own diagnostic on the frozen source copy, and states that a pinned-revision diagnostic is unavailable. A real migration therefore left thirteen obligations undecidable. The instruction and its checker recipe now ask for the pinned procedures and the recorded current source diagnostic. The guide already used that wording, and no other requirement of the instruction changed.

The catalog checker accepted the new text and refused two planted reverts. The checklist test kept every step sentence within thirty words. An independent review judged that the thirteen obligations become decidable from evidence the job already records.

## Evidence limits

The affected test families passed after each change, including 231 migration tests, 22 record-tool tests and 198 lint-row tests. The ledger gate against 10.5.1 reports seven added rules and no changed or deleted rule. Three are behavioral rules without held-out evidence: the orphan-terminal repair, the diagnosis preflight and the README carrier. Four are mechanical safety invariants with owner-accepted gate exceptions. They cover the stamp preconditions, the active-decision definition, the retained selection and lifecycle records, and the closed-task receipt hold. The script manifest and the unit dispositions record the new script digests. These are deterministic checks of the shipped scripts on macOS; they do not measure agent behavior.

The evaluation effect oracle now finishes a capture when the system refuses a group signal after the leader has exited. An earlier release run failed once on that refusal. The oracle is evaluation tooling and is not installed.
