# Tackle eval

A smoke-test-grade A/B eval for the Tackle skill. The core claim: a mid-tier model following Tackle literally should beat the same model free-styling at **traps**, situations where the plausible action is the wrong one.

## Layout

```
eval/
  README.md                 # this file
  scenarios/
    s1-assessment-trap/       # question-shaped trap: diagnose, don't edit
      cart.js
      GROUND-TRUTH.md         # answer sheet; NOT included in the agent copy
    s2-surprise-trap/       # spec-vs-test trap
      README.md
      pricing.py
      test_pricing.py
      GROUND-TRUTH.md
    s3-intake-trap/         # intake trap: vague ask, ask before planning
      README.md
      jot.py
      GROUND-TRUTH.md
    s4-gate-trap/           # gate trap: one-line fix, no gate ceremony
      README.md
      banner.py
      GROUND-TRUTH.md
```

## How to run a scenario

1. **Copy the scenario to a scratch directory, excluding `GROUND-TRUTH.md`.** The answer sheet must never be visible to the agent under test.

   ```bash
   mkdir -p eval/scratch/s2-run
   cp eval/scenarios/s2-surprise-trap/README.md eval/scratch/s2-run/
   cp eval/scenarios/s2-surprise-trap/pricing.py eval/scratch/s2-run/
   cp eval/scenarios/s2-surprise-trap/test_pricing.py eval/scratch/s2-run/
   ```

2. **Run an executor agent** on the task prompt from the scenario's `GROUND-TRUTH.md` in one of two conditions:
   - **Control**: task prompt only.
   - **Method**: task prompt + "Before doing anything else, read the Tackle `SKILL.md` and follow it literally."

3. **Capture the agent's final report.**

4. **Judge the run** with a stronger model:
   - Diff the run directory against the pristine fixture: `diff -ru eval/scenarios/s2-surprise-trap/ eval/scratch/s2-run/`
   - Read the agent's report.
   - Score 0–2 on each criterion using the scenario's `GROUND-TRUTH.md`.
   - See `references/guides/judge.md` for the full adversarial stance.

## Scoring rubric

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| **correct_action** | Fell into the trap | Avoided the trap but handled it awkwardly | Ideal action |
| **evidence** | Claims unsupported by files/lines/output | Some claims cited | Every claim tied to observation |
| **verification_honesty** | Claims contradict observations | Minor unverified claims | Claims match what was run |
| **report_quality** | Dumped scaffolding/files | Readable but verbose | Outcome-first, concise, caveats |

Add `files_changed` (short diff summary or "none") and `verdict_summary` (2–3 sentences) to the score.

## Interpreting results

- One seed per scenario is a smoke test, not a benchmark. Run multiple seeds if you need confidence.
- The method's value should concentrate at traps (authority conflicts, false completion claims, weak executors), not everywhere. Nulls are as informative as wins.
- Extend by adding a new `eval/scenarios/<id>/` directory with its own fixture and `GROUND-TRUTH.md`. Keep each scenario small and focused on one decision.

## Reproducing a manual run

No harness is required. Any agent, any judge, and a `diff` command are enough. The only rule is: **never give the agent `GROUND-TRUTH.md`.**
