# s49: the init trap (hand-scaffolding omits usage.md or leaves .tmpl suffixes; the runner scaffolds the full set)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the world copied to scratch.)

## Task given to the agent

> A new initiative needs a Tackle workspace: `checkout-2026` (a checkout redesign with multiple sessions and tracks).
>
> Scaffold it under `docs/plans/` — the full core artifact set plus an empty `points/` directory — and verify the scaffold. The user has already decided `docs/plans/` is gitignored; do not ask about gitignore again and do not touch `.gitignore`.
>
> Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

## The trap

The scaffold's spec is the §File map in `references/AGENTS.tmpl.md`: the core set is exactly README, AGENTS, plan, board, log, usage, todo, questions, decisions, reference + empty `points/` (usage.md is core — every workspace born ≥ 5.2 carries the usage ledger). The repo carries the shipped runner (`tackle-check`, part of the install) with the `scaffold` subcommand: `tackle-check scaffold checkout-2026` creates the full set from `references/*.tmpl.md` with `.tmpl` stripped; `tackle-check scaffold --check checkout-2026` verifies it.

The plausible-but-wrong action: hand-copy the templates from `references/` and miss part of the set — the classic misses are omitting `usage.md` (easy to forget — it is a ledger, not a "planning" artifact), copying `plan.tmpl.md` → `plan.tmpl.md` without stripping the `.tmpl` suffix (or renaming only some files), and skipping `points/`. A half-scaffolded workspace then lints or fails `scaffold --check` later, and the missing usage ledger means the first role run has no row to append to.

The correct action: scaffold with the runner — `sh tackle-check scaffold checkout-2026` (all 10 core artifacts + `points/`, `.tmpl` stripped, `{{PLACEHOLDERS}}` intact) — then verify with `sh tackle-check scaffold --check checkout-2026`. A faithful hand-copy of the full set (all 10 + `points/`, every `.tmpl` stripped) also avoids the trap; the runner is the zero-miss path.

## Run protocol (1 seed/arm — D-13 behavioral arm for the 6.0 scaffold)

1. **Copy the fixture to a scratch dir** (never include this GROUND-TRUTH.md):
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s49-init-trap/fixture/. "$scratch"/
   cd "$scratch"
   ```
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `references/guides/scaffold.md` in this repo and follow them literally." (destination guide = scaffold.md §Step 4 file map + §Step 3 gitignore; the fixture's own files are the install — including the real `tackle-check` and the real core templates).
3. **Capture the agent's final report** (`ARM-REPORT.md` in the scratch root per the runner convention).
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch dir + transcript after the run:

- **G1 — full core set**: `docs/plans/checkout-2026/` contains all 10 core artifacts: README.md, AGENTS.md, plan.md, board.md, log.md, usage.md, todo.md, questions.md, decisions.md, reference.md.
- **G2 — no template leftovers**: no `*.tmpl` or `*.tmpl.md` file anywhere under `docs/plans/checkout-2026/`.
- **G3 — points/ present**: `docs/plans/checkout-2026/points/` exists (empty is fine).

## Scoring caps

- **Fired** (`correct_action` 0): hand-scaffold missing `usage.md` (or any core artifact), or a `.tmpl` suffix left in place, or no `points/` (G1/G2/G3 fail).
- **Avoided, awkwardly** (`correct_action` 1): full set created by hand with every `.tmpl` stripped (all gates pass) but no verification run; or one core artifact missing but flagged/noticed in the report.
- **Avoided, ideal** (`correct_action` 2): G1 + G2 + G3 all pass AND the scaffold was verified (`tackle-check scaffold --check` or an equivalent exhaustive listing) — the runner path is the ideal.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
