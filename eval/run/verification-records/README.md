# Verification record lifecycle regression

`test_records.py` extracts and executes the actual Python blocks shipped in Markdown. Tests use
temporary directories; they never retire or compact existing user evidence. The fixture covers
separate actual executions with shared bytes, changed revisions, explicit workspace boundaries,
recursive-selector exclusion and bounded prior-record snapshots, corrupt/missing objects,
storage failure/interruption, concurrency, protected-reference retention, retirement, legacy
reads and portable export/restoration. Existing execution-controls, grey-fixes and lite-closure
suites retain their original assertions; the latter two pass the newly required workspace.

Run the target with `python3 -m unittest discover -s eval/run/verification-records -p 'test_*.py' -v`.
CI discovers this family through the central registry and checks its nonzero test count.

The storage-savings comparison script, measured against a fixed baseline commit, was removed;
git history keeps its record.

These are deterministic recipe tests, not agent-decision evaluations or real-workspace savings
estimates. Agent read telemetry and billed tokens remain unavailable. The recipe relies on
filesystem symlinks, atomic same-filesystem publication and directory sync; unsupported hosts
need a complete equivalent native capture rather than a false portability claim.
