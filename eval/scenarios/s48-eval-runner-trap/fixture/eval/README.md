# Tackle eval

A smoke-test-grade A/B eval for the Tackle skill: a mid-tier model following Tackle literally should beat the same model free-styling at **traps**, situations where the plausible action is the wrong one.

## Running a scenario — runner-assisted (mechanized path, Tackle 6.0)

The shipped `tackle-check` runner mechanizes the suite flow; the manual steps are the fallback for hosts without the runner. `tackle-check eval` never executes an LLM or agent arm — it prepares, captures, audits, and validates; the strong-model judgment stays an agent step.

1. **Prepare** — `sh tackle-check eval prepare <scenario> [--seeds N]` (default N=1) stages one scratch per arm (`eval/scratch/<scenario>-<arm>-<seed>/`; the world is `fixture/` flattened when present, else every scenario file except `GROUND-TRUTH.md` — the answer sheet never reaches an arm) and prints the run sheet.
2. **Run the arms** — fresh executors on the task prompt (control) / task prompt + method addendum (method). **The executor writes its final report to `<scratch>/ARM-REPORT.md`**.
3. **Diff** — `sh tackle-check eval diff <scenario>` stages a pristine and diffs each arm. Informational; the only FAIL is the scenario's own answer sheet leaked at an arm root.
4. **Audit** — `sh tackle-check eval audit <scenario>` checks the mechanical arm compliance (both arms staged, `ARM-REPORT.md` present, no top-level answer-sheet leak, no world file missing) and prints the model-only transcript items.

The one absolute rule: **the executor never sees `GROUND-TRUTH.md`** — and staging is where leaks happen.

## How to run a scenario manually (fallback)

1. Copy the scenario to a scratch directory, **excluding `GROUND-TRUTH.md`**. The answer sheet must never be visible to the agent under test.
2. Run an executor agent on the task prompt from the scenario's `GROUND-TRUTH.md` in one of two conditions: control = task prompt only; method = task prompt + "Before doing anything else, read the Tackle `SKILL.md` and follow it literally."
3. Capture the agent's final report.
4. Judge the run with a stronger model: audit arm compliance first, diff the run directory against the pristine fixture (`diff -ru`), read the report, score 0–2 per criterion.
