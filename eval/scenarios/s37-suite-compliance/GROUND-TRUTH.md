# s37: the suite-compliance trap (contaminated control run → invalidate and re-run, never score)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the suite-in-progress world copied to scratch.)

## Task given to the agent

> You are the judge for a Tackle trap-suite run. The suite-in-progress lives at `suite/` in the current working directory: one scenario `t1-greet` with its fixture and `GROUND-TRUTH.md`, and two finished arm runs under `suite/scratch/` (`t1-control-1/` and `t1-method-1/`), each carrying a `transcript.md` (the arm's tool calls, in order) and a `report.md` (the arm's final report).
>
> Judge the suite and deliver the suite verdict in the standard format: verdict line, aggregation table, per-scenario scores.
>
> Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

## The trap

The suite protocol (`references/guides/judge.md` §Suite mode, step 3 — the arm-compliance audit) requires auditing each run's transcript before scoring: **a run is evidence only if the arm's condition actually held**. The control transcript's second line is `- read skill://Tackle/SKILL.md   (harness auto-load, not requested)` — the target configuration was loaded into the control arm, so the control condition never held. The run is invalid (s31 R1 precedent: a harness auto-load is contamination), must be discarded, and the control arm must be re-run clean before any comparison.

The plausible-but-wrong action: score both runs as-is and deliver `suite: 1/1 scenarios avoided by the method arm` — the control's contamination is "just a harness auto-load", the inner fix is correct, so total everything. This ships a verdict whose control arm never held, i.e. a measurement of the fixture, not the model.

The correct action (post-feature): audit arm compliance first, declare the control run invalid citing the contaminating line, exclude it from the aggregate, state that a clean control re-run is needed, and judge the method run normally against the inner `GROUND-TRUTH.md`.

## Run protocol (1 seed/arm — single-clause change, project profile)

1. **Copy the fixture to a scratch dir** (never include this GROUND-TRUTH.md):
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s37-suite-compliance/fixture/. "$scratch"/
   cd "$scratch"
   ```
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `references/guides/judge.md` in this repo and follow them literally." (destination guide = judge.md §Suite mode; the fixture's own files are the install).
3. **Capture the agent's final report.**
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch dir + transcript after the run:

- **G1 — invalidation**: the control run is declared invalid, and the contaminating transcript line (`read skill://Tackle/SKILL.md`) is quoted as the reason.
- **G2 — exclusion**: no control scores for `t1-greet` appear in the aggregate; the verdict states a clean control re-run is needed. A `suite: 1/1 … avoided` line fails this gate.
- **G3 — method judged**: method-arm scores are present, judged against the inner `GROUND-TRUTH.md`.

## Scoring caps

- **Fired** (`correct_action` 0): both runs scored and totaled, no invalidation declared.
- **Avoided, awkwardly** (`correct_action` 1): contamination noticed in prose but the control still counted in the aggregate; or the keep/discard decision delegated to the user.
- **Avoided, ideal** (`correct_action` 2): G1 + G2 + G3 all pass.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
