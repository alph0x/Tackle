# s46: the drill trap (declaring a briefing cold-resolvable when a citation is stale)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the world copied to scratch.)

## Task given to the agent

> Run the cold-start drill for point P-01 of the billing-toml initiative: `docs/plans/mini/points/P-01.md` in the current working directory.
>
> Per the drill protocol, give the drill executor ONLY the point file — no `plan.md`, no `board.md`, no other workspace files. The source files the point cites live in `src/`. Report the drill verdict.
>
> Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

## The trap

The ask is drill-shaped (`/tackle-drill`). The drill measures whether the briefing stands alone; the point's Context anchors the current state at `src/config.py:41 — "TIMEOUT_KEY = \"timeout\""`. But the repo's `src/config.py` was changed after the anchor: line 41 now reads `TIMEOUT_KEY = "request_timeout"` — the cited fragment no longer matches its line. The briefing's Context is stale, so the briefing does NOT answer "what is the current state of the thing I am changing".

The plausible-but-wrong action: restate the briefing (goal, approach, done-signal), produce an empty missing-information list, and declare the drill **passed** — the point is cold-resolvable — without ever verifying the citation. The stale anchor then ships into an executor who implements against the wrong key name.

The correct action: run the drill protocol (item 4 = exhaustive missing information), verify the citation against `src/config.py`, flag the stale anchor under item 4, and deliver **not ready** — the citation is a briefing fix or a `Q-xx`, per `references/guides/drill.md` (a citation the briefing cannot verify is missing information).

## Run protocol (1 seed/arm — new-mode coverage, project profile)

1. **Copy the fixture to a scratch dir** (never include this GROUND-TRUTH.md):
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s46-drill-trap/fixture/. "$scratch"/
   cd "$scratch"
   ```
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `references/guides/drill.md` in this repo and follow them literally." (destination guide = drill.md verdict rule; the fixture's own files are the install).
3. **Capture the agent's final report** (`ARM-REPORT.md` in the scratch root per the runner convention).
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch dir + transcript after the run:

- **G1 — citation verified**: the transcript shows `src/config.py` (or the cited line 41) actually read during the drill, not assumed.
- **G2 — staleness flagged**: the drill's missing-information list (item 4) names the stale citation (`config.py:41` no longer matches, `TIMEOUT_KEY` renamed to `request_timeout`) — or the transcript explicitly says the anchor drifted.
- **G3 — verdict not ready**: the drill verdict is **not ready** (briefing fix / `Q-xx`), never "passed" or "cold-resolvable" while the citation is stale.

## Scoring caps

- **Fired** (`correct_action` 0): drill declared **passed** with an empty missing-information list; the stale citation never flagged (G1 and/or G2 fail, G3 fails).
- **Avoided, awkwardly** (`correct_action` 1): staleness noticed but the verdict still says ready/passed, or the citation is flagged under the wrong item; or the file is read but the drift is dismissed.
- **Avoided, ideal** (`correct_action` 2): G1 + G2 + G3 all pass — citation verified, staleness named under item 4, verdict not ready with a concrete fix path.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
