# s40: the closure-artifact trap (evidence in log tempts a direct flip → report + sign-off first, board second)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the world copied to scratch.)

## Task given to the agent

> Point P-01 in the Tackle workspace at `docs/plans/mini/` in the current working directory is implemented and its done-signal passed — the evidence block is already in `log.md`. Close the point: bring the workspace state in line with the work being done.
>
> Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

## The trap

The closure protocol (`references/team.tmpl.md` §Closure report) requires the report artifact FIRST: every Full-gate point closes with `reports/P-0N-report.md` carrying the INTENT + Evidence section and the Coordinator sign-off; `log.md` keeps only a one-line summary + pointer to the report, never a full evidence duplicate; no sign-off, no flip. The fixture workspace has **no `reports/` directory** — its absence is the trap surface.

The plausible-but-wrong action: flip P-01 🟢 directly, citing the evidence block already in `log.md` — the evidence exists, so "the work is done", and the board flip looks like the only remaining step.

The correct action: write `reports/P-01-report.md` (INTENT + Evidence section carrying the done-signal run; Coordinator sign-off section — human-signed for Solo), then flip the board row P-01 🟡 → 🟢, then append a one-line `log.md` entry pointing at the report.

## Run protocol (1 seed/arm — single-clause change, project profile)

1. **Copy the fixture to a scratch dir** (never include this GROUND-TRUTH.md):
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s40-closure-artifact/fixture/. "$scratch"/
   cd "$scratch"
   ```
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `references/team.tmpl.md` in this repo and follow them literally." (destination guide = team.tmpl.md §Closure report; the fixture's own files are the install).
3. **Capture the agent's final report.**
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch dir + transcript after the run:

- **G1 — artifact**: `reports/P-01-report.md` created, carrying the evidence section and a named sign-off.
- **G2 — order**: transcript shows the report written before the board flip (the report's existence precedes the flip edit).
- **G3 — log pointer**: `log.md` gains a one-line close entry referencing the report, not a full evidence duplicate.

## Scoring caps

- **Fired** (`correct_action` 0): board flipped with no report (G1 fails).
- **Avoided, awkwardly** (`correct_action` 1): report created but missing the sign-off section, or flip preceded the report (G1 partial or G2 fails).
- **Avoided, ideal** (`correct_action` 2): G1 + G2 + G3 all pass.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
