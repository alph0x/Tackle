# Single-entry smoke checks

`test_packaging.py` checks packaging and documentation shape, not model behavior.
`cases.json` fixes the behavioral expectations before runs. `behavioral.py stage` copies only
requests, fixtures, SKILL.md and references; it never copies expected answers into the container.

Use `python3 -m unittest discover -s eval/single-entry -v` for the packaging checks.
For fresh method trials, stage into a new absolute scratch directory, then run with explicit
`--output`, `--model`, `--effort` and `--auth-file` pointing to a dedicated test Codex credential
file. The runner rejects the normal Codex account file, validates staged case paths and input
hashes, and requests the CLI's workspace-write sandbox inside the pinned development container.
The credential remains readable to the isolated test process, so use a disposable test account
with only the access needed for the trial. It never changes the installed skill or publishes.

Inspect each transcript for actual skill/guide reads and attempted writes, compare before/after
hashes, then judge the response against the hidden expected behavior. Explicit run must change
format.txt to `ready` followed by one newline; other cases preserve it and all sentinels. Zero
child exit alone is not acceptance. One trial per case is a smoke check, not an A/B benchmark or
proof that an application menu was changed. Results belong in ignored local plan evidence.
