# Tackle 10.6.0 checks and evidence limits

## Command declarations

The brief-reader checks cover working directory, native success condition and evidence destination. Separate cases cover live declarations, illustrative fenced examples and indented code. These checks exercise the reader on those inputs.

## Consent and command capture

The state checks cover multipart task IDs and preservation of existing regular-file permissions. The command-capture and lint-runner checks exercise malformed arguments and invalid timeouts before command launch.

## Owned process cleanup

The process-effect tests exercise two outcomes after a permission denial. The cleanup handler accepts confirmed absence of the owned process group and reports unresolved denial when the group can still exist.

The GPT route interruption test still uses a fixed 150 ms delay before sending the termination signal. The exact point at which the signal arrives remains unverified.

## Release prerequisites

The mechanical replay records the failing command and its exit status. The release-step checks cover stopping subsequent steps after a failed prerequisite. Hosted CI and publication have separate records.

## Migration review

The release checks used controlled workspaces for adoption, repeat adoption and restoration. On an authentic active workspace, migration stopped when closed task records did not meet the required format. Adoption and restoration of an authentic active workspace remain unverified.

The observed migration checked an existing marker beside the working copy. Its creation by the migration procedure remains unverified.

The 10.7 migration work carries two verification obligations. The first is to observe the applicable procedure creating the rollback marker. The second is to verify, adopt, repeat adoption without further effects, and restore an eligible active workspace byte for byte while preserving the original and its neighbors.

The real case retained the authoritative original, the prepared candidate, the board and the file inventory. Independent review accounted for the current catalog instructions and their source references. Historical provenance still requires separate evidence.

R-MIGRATE-22 requires a recorded decision before a file without a current counterpart is retained as historical data or mapped to a current artifact. It remains behaviorally untested.

## Release rule evidence

R-REL-31 and R-REL-32 retain their existing statements and complete ledger entries in this release. Their evidence remains untested. A pre-existing evidence gap and a possible safety-invariant concern around checkout provenance and private workspace text remain unresolved. This release neither reclassifies the entries nor establishes universal agent behavior. Their proposed timing changes remain deferred for future planning.

## Installed guidance and task templates

On the accepted guidance candidate, the worked example ran four tests. Its review detected both zero discoveries and a command masking a failure. Eight checks resolved template and installed-resource references. The entry contained 1,120 words, the RUN card 1,045, and the approved reading chain 4,941. Both registry invocations passed 43 families and 2,521 tests with zero skips on that candidate.

R-EVID-27 guides suite judging when repository scenarios are unavailable. R-PLAN-47 describes writable paths and shipped paths in the task template. The R-RUN-14 statement now also covers the testing guide's existing ban on writing a unit test after implementing the behavior it covers, even under a general test-first opt-out. The three remain behaviorally untested. Native Windows execution and the dedicated judge calibration remain unverified.

## Retrospective measurements

Twenty session cases exercised the installed recipe, including shared identifiers, missing records, duplicate measurements, measured zeroes and conflicts. Five cases supplied the same files to lint and the retrospective. On the accepted retrospective candidate, both full registry invocations passed 43 families and 2,523 tests with zero skips. The rule has mechanical coverage. Agent compliance remains untested.

## Plan view sessions

A registry test renders a recorded session with a start and no end in English and Spanish. It checks the open-session label and the heading that marks current activity as unconfirmed. It also checks that the session label no longer uses the running or in-progress wording, which remains available for task state. R-STATUS-33 remains untested.

## Plan view board links

The board reader opens the workspace folder and its task board without following links, relative to the parent directory. The view tests cover a board link to an outside file, a linked workspace folder, a linked board at the public entry point, a linked sibling folder and a linked initiative member board. In each case the outside file's bytes, inode, mode and timestamps stay unchanged. A refused board in a single-workspace build exits with status 2 and one `cannot read the task board` line. A refused board keeps a currency check stale. Sibling and initiative refusals keep their existing messages. A further test builds and checks a workspace under a linked parent directory. The affected view tests pass with a temporary directory reached through a link, as on macOS by default.

A declared sibling outside an initiative whose folder is a link uses the same reader but has no dedicated test. If an initiative member's board is replaced by a link between its two reads, the view stops with an error instead of a refusal; the link target is still not read. The parent directory must be readable, not only searchable.

## Workspace board checks

The standalone lint checks retain their previous file-reading behavior. Confinement of board reads to the selected workspace remains an open limitation for thirteen checks. The plan-view reader has separate coverage.
