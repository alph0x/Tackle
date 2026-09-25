# Single-entry smoke checks

`test_packaging.py` checks packaging and documentation shape, not model behavior.
`cases.json` fixes the behavioral expectations before runs. `behavioral.py stage` copies only
requests, fixtures, SKILL.md and references; it never copies expected answers into the container.

Use `python3 -m unittest discover -s eval/single-entry -v` for the packaging checks.

Model runs moved to [`eval/protocol-v2/PROTOCOL.md`](../protocol-v2/PROTOCOL.md); `run` is retired
here. It exits 2 with a pointer to that harness and starts no process — no credential is ever
mounted, copied or passed into a participant environment by this file (R14, D-45). `stage` and the
isolation probe in `run_case` are unaffected historical tooling: staging still copies only requests,
fixtures, `SKILL.md` and references (never expected answers), and the probe still verifies container
isolation without ever invoking a model.
