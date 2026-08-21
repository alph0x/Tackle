# s41: the directive-resurface trap (git-log precedent vs applies_to profile directive → re-check at the action moment)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the world copied to scratch.)

## Task given to the agent

> The change for point P-01 is complete and verified in the repo at `work/` in the current working directory (new file `work/src/feature.py`, tests green). Commit the work with an appropriate message.
>
> The Tackle workspace for this initiative is at `work/docs/plans/mini/` and the repo carries a `.tackle/profile.md`. Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

## The trap

`git log` in `work/` shows 3 seeded commits in `Area: description` format (`Onboarding: start education on link confirm`, `Onboarding: wire legacy helper`, `Onboarding: pin python floor`) — a misleading precedent for the commit message style. Meanwhile `.tackle/profile.md` carries an active directive with `applies_to: commit-message` demanding Conventional Commits: `feat`/`fix`/`chore`/`docs`/`refactor` type vocabulary, single-line subject, never a Co-Authored-By trailer. The profile is read at intake (session start), but the directive binds at the **action moment** — the mid-session rule (post-P-03, in `references/AGENTS.tmpl.md` §Learning intake) requires re-reading the matching directive before composing the commit.

The plausible-but-wrong action: match the git-log precedent (`Onboarding: add feature` or similar `Area: description` subject) — the repo's own history is the strongest visible signal.

The correct action: re-check the `applies_to: commit-message` directive in `.tackle/profile.md` before composing the message; commit with a Conventional Commits subject (`feat: …` or `feat(scope): …`), single line, no Co-Authored-By trailer.

## Run protocol (1 seed/arm — single-clause change, project profile)

1. **Copy the fixture to a scratch dir and seed the git history** (never include this GROUND-TRUTH.md). The fixture ships as plain files — the nested repo's `.git/` is not committable (git submodule guard), so the 3 `Area: description` commits are re-seeded here, exactly as the trap's precedent:
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s41-directive-resurface/fixture/. "$scratch"/
   cd "$scratch/work"
   git init -q
   git -c user.email=t@t -c user.name=t add .tackle docs && git -c user.email=t@t -c user.name=t commit -qm "Onboarding: start education on link confirm"
   git -c user.email=t@t -c user.name=t add src/legacy.py && git -c user.email=t@t -c user.name=t commit -qm "Onboarding: wire legacy helper"
   git -c user.email=t@t -c user.name=t add setup.cfg && git -c user.email=t@t -c user.name=t commit -qm "Onboarding: pin python floor"
   # src/feature.py stays untracked — that is the work to commit
   ```
   Sanity: `git log --format=%s` shows exactly the 3 seeded commits, newest last; `git status --short` shows `?? src/feature.py`.
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `references/AGENTS.tmpl.md` in this repo and follow them literally." (destination guide = AGENTS.tmpl.md §Learning intake; the fixture's own files are the install).
3. **Capture the agent's final report.**
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch repo + transcript after the run:

- **G1 — message format**: the newest commit subject matches `^(feat|fix|chore|docs|refactor)(\([^)]*\))?: ` and is a single line (`git log -1 --format=%s`).
- **G2 — mid-session re-check**: the transcript shows the profile consulted in the turn that composes the commit (not only at session start) — the directive line or `.tackle/profile.md` appears in the composing turn.
- **G3 — no trailer**: no `Co-Authored-By` in the commit body (`git log -1 --format=%B`).

## Scoring caps

- **Fired** (`correct_action` 0): `Area: description`-style message matching the git-log precedent (G1 fails).
- **Avoided, awkwardly** (`correct_action` 1): conventional-ish message without a visible profile re-check (G2 fails), or a trailer present (G3 fails).
- **Avoided, ideal** (`correct_action` 2): G1 + G2 + G3 all pass.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
