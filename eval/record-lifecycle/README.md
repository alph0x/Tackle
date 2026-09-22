# Verification record lifecycle regression

`test_records.py` extracts and executes the actual Python blocks shipped in Markdown. Tests use
temporary directories; they never retire or compact existing user evidence. The fixture covers
separate actual executions with shared bytes, changed revisions, explicit workspace boundaries,
recursive-selector exclusion and bounded prior-record snapshots, corrupt/missing objects,
storage failure/interruption, concurrency, protected-reference retention, retirement, legacy
reads and portable export/restoration. Existing execution-controls, grey-fixes and lite-closure
suites retain their original assertions; the latter two pass the newly required workspace.

Run the target with `python3 -m unittest discover -s eval/record-lifecycle -p 'test_*.py' -v`.
CI discovers this family through the central registry and checks its nonzero test count.

`python3 eval/record-lifecycle/measure.py /tmp/storage-measurement.json` compares the baseline
recipe pinned at commit `61f9b4b` (8.1.0) to the current Markdown recipe. Each side executes
three real checks of one unchanged 1 MiB input. It reports all stored file bytes, unique bytes,
classes, aliases, allocated blocks where exposed, and observed capture wall time. The candidate
then captures a changed input and retires the first three events under a disposable policy,
preserving compact original event/outcome/provenance tombstones and the complete current record.
It separately reports metadata reclaimed after tombstone cost and unchanged logical history. Maintenance time and resulting storage
are included. Equal evidentiary scope matters more than any arbitrary reduction target.

`--inventory /absolute/path/to/evidence` performs a read-only inventory instead. Hashes have no
size cutoff. Classes derive from raw record mappings when available; shared bytes are counted
once under the documented precedence. Unclassified artifacts and current/historical status
remain explicit when a directory lacks a complete obligation/retention policy. Identical-copy
bytes are a measurement, never authorization or proof that bytes can be deleted.

These are deterministic recipe tests and synthetic measurements, not agent-decision evaluations
or real-workspace savings estimates. Agent read telemetry and billed tokens remain unavailable.
The recipe relies on filesystem symlinks, atomic same-filesystem publication and directory sync;
unsupported hosts need a complete equivalent native capture rather than a false portability claim.
