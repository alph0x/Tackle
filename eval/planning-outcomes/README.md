# Planning outcomes

Three small feature requests against fixture repositories, planned and executed end to end by a
participant and judged mechanically by hidden acceptance tests: `s62-caller-contract`,
`s63-documented-edge-rule` and `s64-stored-data-compat`. Each has a development variant `v1` and a
held-out variant `h1`. They measure whether the method changes the outcome or the cost of real
planning; they test no single rule. They verify fixtures and the judge, not agent behavior.

```sh
python3 -m unittest discover -s eval/planning-outcomes -p 'test_*.py' -v
python3 eval/planning-outcomes/judge.py --episode <harness episode dir>
python3 eval/planning-outcomes/judge.py --scenario <scenario_id> --variant <variant_id> --work <dir> --out <file>
```

## Variant layout

Beside the usual `input/` (the participant's `task.md` and `fixture/`) and `GROUND-TRUTH.md`, each
variant holds:

- `hidden/`: `hidden.json` and the hidden tests, `test_*.py`. They never reach the participant: staging
  copies only `input/`.
- `reference/a/` and `reference/b/`: two independently written solutions, as overlay trees copied over
  the fixture. Every overlay file differs from the fixture file it replaces.

`hidden.json` is `{"schema": "tackle-hidden-tests/1", "tests": <exact count>, "timeout_seconds": <int>,
"pythonpath": [<entries relative to the fixture root>], "visible": [<the fixture's own test command>] | null}`.

## The judge

- **Inputs.** The hidden tree comes from the git index of `--repo` (default: this repository), at
  `eval/scenarios/<scenario_id>/variants/<variant_id>/hidden/`; the working tree does not affect a
  judgment. Episode mode reads `scenario_id` and `variant_id` from `stage.json`, `adapter` from
  `run.json`, the tree under `work/` and `sessions/NN/stdout`. It never reads the arm.
- **Isolation.** The judge copies the work tree to a scratch directory and never writes the judged
  tree. It runs `runner.py` as `python3 -I runner.py <hidden dir> <copy> <result file> <pythonpath…>`.
  Isolated mode ignores `PYTHONPATH`, the working directory and `sitecustomize`; the runner checks that
  `unittest` is the standard library's, appends the pythonpath entries after the standard library,
  discovers the suite programmatically and writes its counts to the result file. The run has a minimal
  environment and `timeout_seconds`; on expiry the process group is killed.
- **Outcome.** `avoided` only when the runner exits 0 and wrote its result, `ran` equals `tests`, and
  there are no failures, errors or skips. Otherwise `fell`; a timeout or a missing result is `fell`.
  `correct_action` is 2 or 0; the other scores are null, because a mechanical judge cannot score them.
  `rule_exposure` is false until an audit says otherwise (PROTOCOL.md §3).
- **Output.** The keys `harness.py record --judgment` reads (`judge`, `outcome`, `invalid_reason`,
  `rule_exposure`, `scores`) plus `details`: the digests of the hidden tree and of the judged tree, the
  hidden-test counts, and the transcript counts. `details` holds counts only, never test output or test
  names. In episode mode the judgment is written to `<episode>/judgment.json`, which stays with the
  episode; cohort report scripts read the details there. An existing output is never overwritten.
- **Transcript counts.** A check run is a shell command matching
  `\b(unittest|pytest|nose2|tox|nox|make\s+(test|check))\b`. Claude Code `stream-json` pairs a `Bash`
  `tool_use` with its `tool_result` (`is_error` marks a failed run); Codex `--json` reads
  `item.completed` `command_execution` items and their `exit_code`. A subagent episode (D-87) is a Claude
  Code session transcript and uses the same parser. `correction_cycles` counts the failing
  check runs followed by a later check run. The fake agent's format, an unknown adapter or an unreadable
  transcript gives `n/a`; direct mode has no transcript. Both parsers are tested on synthetic streams
  only: their fidelity to real host output is unverified until an authorized smoke episode.
- **Refusals.** Exit 2 with `judge: refused: <reason>` and no output for an unknown variant, a missing or
  malformed `hidden.json`, a `--repo` that is not a git work tree, or a missing work tree. A judge
  failure never becomes an episode outcome. `--debug` prints the runner's test output; it is never used
  on a held-out variant while the method is being tuned.
- **Residual.** Participant code runs inside the runner's process, so a deliberately adversarial
  participant is out of scope.

Python 3.10 or later (the tests use `sys.stdlib_module_names`).
