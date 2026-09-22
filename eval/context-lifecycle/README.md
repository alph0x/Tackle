# Context lifecycle regression and synthetic measurements

Run `python3 -m unittest discover -s eval/context-lifecycle -p 'test_*.py' -v` from the
repository root. Tests extract and execute the Python block in the installed
`references/guides/context-lifecycle.md`; no separately maintained surrogate implements it.
Run `python3 eval/context-lifecycle/benchmark.py` to reproduce `measurements.json`.

Coverage includes source/scope/membership invalidation; tampered projections; old binding
decisions; archived failed attempts and original-heading lookup; missing/corrupt originals;
single-writer refusal; recoverable rotation at all publish boundaries; interrupted completion;
idempotent final-event retry; selected legacy archive adoption; and portable source export.
The immutable expected original bytes are created before running the candidate recipe.

The 10/100/1,000-task comparison measures **logical content bytes**, with the same active task
and dependencies. Closed task-board rows deliberately grow; the candidate rehashes the entire
authoritative board. The baseline executes a complete-file latest-entry scan and the pinned
8.1.0 whole-history handoff algorithm, followed by a board update/history append. This is a
specified algorithm comparison, not a measurement of all baseline agent behavior.

Each result includes initial retained size; resume, update and handoff reads/writes; indexing and
archive writes; projection construction; named old failure retrieval; full reconstruction;
post-maintenance retention/file count; and a complete scenario total. Both algorithms pay for
the same retrieval and reconstruction requests. Recipe hashing, index traversal, staged-file
bytes, source copies and export verification are included. Metadata calls are separate; physical
filesystem/cache/journal costs are unmeasured. No extra check-record objects occur in these I/O
fixtures; their transitive export is covered separately by the storage family and integration test.

The measured routine resume and handoff reads are smaller for 100 and 1,000 closed tasks, but
the initial maintenance/reconstruction scenario is more expensive than the original layout.
The 10-task case also spends more on verified handoff. These results support selective use for
repeated long-history continuation, not a universal speedup, constant-cost claim, storage-saving
claim, or agent-compliance claim. Original history is retained and total retained bytes grow.
The example's 64 KiB segment target/five active sessions are measured fixture choices, not a
mandatory cap; active obligations and single original events are never truncated to fit them.

Milestone completeness/readiness belongs to the compiler family. Behavioral comparison and
human comprehension remain a separate, explicitly pending cohort when isolated execution is
unavailable; deterministic tests do not discharge that release obligation.
