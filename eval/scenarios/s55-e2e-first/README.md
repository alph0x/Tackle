# s55 — E2E-first planning and execution trap

**Trap:** a code Task crosses CSV parsing, calculation, CLI invocation and JSON output. The old
testing doctrine mandates an isolated T0 unit layer even when a public-boundary E2E can cover the
whole contract. Does the revised doctrine lead the executor to plan a single E2E check, write it
before implementation, and retain a replayable verification artifact?

Both arms receive `task.md` and `fixture/items.csv` in separate writable scratch directories.
Give the control arm the committed pre-change `references/guides/testing.md`; give the method arm
the edited guide plus its current planning/Task clauses. The prompt instructs each arm to read its
supplied method file, then PLAN and RUN the task; it does not instruct a particular test type.
Never stage `GROUND-TRUTH.md` for an arm. Save the CLI event stream and output for judging.

The method arm passes only when the transcript and resulting files show: check choice recorded
before implementation; E2E calls `receipt.py` as a subprocess with the supplied valid fixture;
the check is written and observed red before product code; no new unit test; green acceptance;
and an artifact that can replay the run with command, inputs, expected/actual, environment, raw
result, and hashes while preserving the original record. Check a missing artifact, an overwritten
record, or an ignored child failure as negative controls.
The control arm is a discrimination signal, not an automatic failure if it independently chooses
good behavior.
