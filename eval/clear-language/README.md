# Clear-language paired evaluation

This development-only harness creates a new current-checkout baseline/candidate
cohort. It preserves the historical Plan → Run comparison unchanged. The fixed
protocol, visible cases and evaluator-only oracle are separate files. Harness
unit tests do not establish agent compliance.

The [8.2 development summary](results-8.2.md) reports completed observations and their limits.
Each future cohort still needs its own execution and independent review records.

The default smoke selects six cases across English and Spanish (12 paired arm
episodes). It covers bounded completion, a status comment during authorized work,
a concrete blocker, obsolete memory, relevant-evidence reuse and integrated failure.
The fixed inventory additionally covers PLAN-only, standalone STATUS, quoted or
negated execution, changed configuration, task-state comprehension and a missing
acceptance obligation. `verify-readonly-es` also checks a repairable stale citation
with protected history under standalone read-only verification. `release-active-v3-en`
checks the active-plus-selected union for a simulated release, preserving selected
workspace global acceptance. Select additional cases explicitly with repeated `--case`.

Run mechanical integrity checks:

```sh
python3 -m unittest discover -s eval/clear-language -p 'test_*.py' -v
```

After the candidate installation is stable, stage into a fresh absolute directory:

```sh
python3 eval/clear-language/runner.py stage /absolute/local/cohort
```

Retain the printed seal outside the evaluated agents' writable environment. Staging
records baseline commit, complete installation/input hashes, protocol/oracle/runner
bytes, cases, seed, budget and randomized arm order. Do not stage until candidate
sources have reached the intended evaluation boundary. Never amend an observed
cohort; changing any frozen input creates a new cohort directory.

A preflight never starts a model and never reads account credentials:

```sh
python3 eval/clear-language/runner.py preflight /absolute/local/cohort \
  --seal RECORDED_SHA256 --output /absolute/local/preflight-results \
  --image sha256:PINNED_LOCAL_IMAGE_DIGEST
```

A missing Docker daemon/image is a recorded PENDING capability limitation, not a
successful behavioral observation. The runner does not install software or pull
images.

Model runs moved to [`eval/protocol-v2/PROTOCOL.md`](../protocol-v2/PROTOCOL.md); `run` is retired
here. It exits 2 with a pointer to that harness and starts no process — no credential is ever
mounted, copied or passed into a participant environment by this file (R14, D-45). `stage` and
`preflight` are unaffected historical tooling: they keep staging sealed cohorts and probing
container isolation without ever invoking a model.

Run results remain outside the sealed cohort. Deterministic artifact checks deliberately
leave semantic behavior UNREVIEWED. An independent evaluator must review actual
transcripts and the protocol rubric; exiting zero or matching a keyword is never
behavioral acceptance. Missing metrics remain n/a with coverage stated.

Read current status from each cohort's execution and independent review records, not this
source template. A focused follow-up may select only affected candidate episodes before sealing;
report it as regression coverage, not a fresh paired comparison. Keep historical inputs/results
unchanged and define retry counts and any acceptance-versus-preservation distinction before execution.
