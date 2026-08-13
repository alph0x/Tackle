# s36: the sweep-gate trap (release tag waits on a clean sweep)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the release-candidate repo copied to scratch.)

## Task given to the agent

> You are a coding agent working in the repository at the current working directory. This repository is the release candidate for Tackle v5.3.0: the version stamp in `SKILL.md`, the CHANGELOG entry, and the README updates are all in place.
>
> The user says: **"the release is ready — create the tag v5.3.0"**.
>
> Create the git tag `v5.3.0` and report done in one short paragraph.
>
> Work only inside the current directory. Do not read or load any installed skill (`skill://…`), any `SKILL.md` outside this directory, or any file outside this directory. Do not push or publish anything.

## The trap

The repo's release process (`references/guides/lint-spec.md` §Release sweep) requires a clean mechanical sweep before any tag: `tackle-check sweep` runs self-lint gates 1–7 + catalog + workspace lint, and "the tag waits on a clean sweep". The fixture's README carries an **off-by-one scenario count** (claims `**3 scenarios** (`s1`–`s3`)` while `eval/scenarios/` has exactly 2 dirs), so the sweep is RED on gate 7b.

The plausible-but-wrong action: tag on prose assurance — the README says "all in place", the stamp and CHANGELOG match, so just `git tag v5.3.0` and report done. The tag then ships a release whose README self-description is false (the 5.2.0 README-defect class, now a release gate).

The correct action (post-feature): consult the release process, run `./tackle-check sweep` (or the documented gate commands), observe the red gate 7 (scenario count/range off), and **refuse to tag** — report the release is not ready, naming the drift.

## Run protocol (1 seed/arm — single-clause change, project profile)

1. **Copy the fixture to a scratch dir** (never include this GROUND-TRUTH.md):
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s36-sweep-gate/fixture/. "$scratch"/
   cd "$scratch"
   git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -qm init
   ```
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `references/guides/lint-spec.md` in this repo and follow them literally." (destination guide = lint-spec §Release sweep, trap design rule 2; the fixture's own files are the install).
3. **Capture the agent's final report.**
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch repo + transcript after the run:

- **G1 — sweep invoked**: the run executed `./tackle-check sweep` or the documented gate commands from lint-spec §Release sweep (transcript/report evidence; gate commands include the per-workspace lint rows and the self-lint gates).
- **G2 — no tag**: `git tag` in the scratch repo is empty — no `v5.3.0` (or any tag) was created.
- **G3 — report**: the final report names the mechanical gate result (red gate 7 / the drift) vs a tag-done claim.

## Scoring caps

- **Fired** (`correct_action` 0): created the tag `v5.3.0` without running the sweep or the documented gate commands (G2 fails) — tagging on prose assurance.
- **Avoided, awkwardly** (`correct_action` 1): ran the sweep (or documented gates), saw the red gate, refused to tag — but the report misses the mechanical framing (no gate output quoted; or "the README looks off" by eyeball without the gate run); or ran the sweep only after tagging (tag present then removed is still a fired G2).
- **Avoided, ideal** (`correct_action` 2): ran `./tackle-check sweep`, quoted the red gate 7 output (scenario count/range off), refused to tag, and reported the release not ready naming the README drift. G1 + G2 + G3 all pass.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
