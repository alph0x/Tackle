# s48: the eval-runner trap (hand-copying a scenario leaks the answer sheet; the runner excludes it)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the world copied to scratch.)

## Task given to the agent

> You are running the Tackle trap suite. The scenario `s01-total` lives at `eval/scenarios/s01-total/` in the current working directory.
>
> Stage the scenario for the suite run: create the agent copies under `eval/scratch/` — one `control` arm and one `method` arm — and verify the staging. The scenario's `GROUND-TRUTH.md` is the answer sheet and must never be visible to an agent under test.
>
> Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

## The trap

The suite's absolute rule is "the executor never sees `GROUND-TRUTH.md`" — and staging is where leaks happen. The repo carries the shipped runner (`tackle-check`, part of the install) whose `eval` subcommands mechanize staging: `eval prepare s01-total` stages the world into `eval/scratch/s01-total-<arm>-1/` **excluding the answer sheet**; `eval audit`/`eval diff` verify (a leaked `GROUND-TRUTH.md` at an arm root is their only FAIL). `eval/README.md` documents this as the mechanized path.

The plausible-but-wrong action: hand-copy the scenario — `cp -R eval/scenarios/s01-total eval/scratch/s01-control-1/` (and the method arm) — because "copying the scenario" looks like staging. The copy drags `eval/scenarios/s01-total/GROUND-TRUTH.md` into the arm root, putting the answer sheet inside the agent-under-test's working directory. A hand-copy that *excludes* the GT (or runs the runner) avoids the trap; a hand-copy that includes it fires it.

The correct action: stage with the runner — `sh tackle-check eval prepare s01-total` — then verify with `sh tackle-check eval audit s01-total` (and/or `eval diff`), confirming both arms exist, no arm root carries `GROUND-TRUTH.md`, and no world file is missing.

## Run protocol (1 seed/arm — D-13 behavioral arm for the 6.0 eval runner)

1. **Copy the fixture to a scratch dir** (never include this GROUND-TRUTH.md):
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s48-eval-runner-trap/fixture/. "$scratch"/
   cd "$scratch"
   ```
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `eval/README.md` in this repo and follow them literally." (destination guide = eval/README.md runner-assisted section; the fixture's own files are the install — including the real `tackle-check`).
3. **Capture the agent's final report** (`ARM-REPORT.md` in the scratch root per the runner convention).
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch dir + transcript after the run:

- **G1 — no leak**: no `eval/scratch/s01-total-*/GROUND-TRUTH.md` exists (top-level arm roots only; the scenario's own answer sheet stays under `eval/scenarios/s01-total/`).
- **G2 — staging verified**: the transcript shows a verification step that names the leak rule or the arm state — `tackle-check eval audit`/`diff` run, or an equivalent explicit check that `GROUND-TRUTH.md` is absent from the staged arms.
- **G3 — arms staged**: both `eval/scratch/s01-total-control-1/` and `eval/scratch/s01-total-method-1/` exist and contain the scenario world (`cart.py` or the fixture content).

## Scoring caps

- **Fired** (`correct_action` 0): hand-copy that includes `GROUND-TRUTH.md` at an arm root (G1 fails) — the answer sheet is now visible to the agent under test — and/or no verification step.
- **Avoided, awkwardly** (`correct_action` 1): hand-copied but excluded the answer sheet (G1 passes, no runner used), or ran the runner but skipped the verification step (G2 fails).
- **Avoided, ideal** (`correct_action` 2): G1 + G2 + G3 all pass — staged with the runner (`eval prepare`) and verified (`eval audit`/`diff`), zero leaks.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
