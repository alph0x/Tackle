# s45: the checklist trap (a generic rubber-stamp checklist, not grounded in the actual work)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the world copied to scratch.)

## Task given to the agent

> Point P-01 in the Tackle workspace at `docs/plans/mini/` in the current working directory is implemented — the discount cap in `src/pricing.py` — and its done-signal passed.
>
> Generate the quality checklist for this work and write it to `docs/plans/mini/checklist.md`. The checklist should reflect what this specific change touches.
>
> Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

## The trap

The ask is checklist-shaped (`/tackle-checklist` → `checklist.md`), and it explicitly demands grounding ("reflect what this specific change touches"). The workspace carries everything the checklist needs: the point briefing (`points/P-01.md` — Touches `src/pricing.py`, done-signal `python -m pytest tests/test_pricing.py`), the log's evidence (5 passing tests incl. the 50% boundary and the over-cap clamp), and the quality-dimensions heuristic (axes fire when Touches match; omit axes that don't fire).

The plausible-but-wrong action: emit a generic boilerplate checklist — "follows the style guide", "code is documented", "no performance regressions", "add unit tests", "update the README", "check security" — that any change in any repo could pass. It names none of this change's actual surface: no `src/pricing.py`, no discount boundary, no done-signal command, no pricing-path regression.

The correct action: read the point briefing, the plan, the board, and the log; write a checklist grounded in the actual work — the discount-cap correctness (the 50% boundary, the over-cap clamp, negative/zero line totals), the done-signal command as the runnable check, the pricing-path regression surface (Touches), and only the quality axes whose heuristic fires (correctness + test depth on money math; security/a11y/i18n axes do NOT fire and are omitted).

## Run protocol (1 seed/arm — new-mode coverage, project profile)

1. **Copy the fixture to a scratch dir** (never include this GROUND-TRUTH.md):
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s45-checklist-trap/fixture/. "$scratch"/
   cd "$scratch"
   ```
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `references/guides/quality-dimensions.md` in this repo and follow them literally." (destination guide = quality-dimensions.md grounding rule; the fixture's own files are the install).
3. **Capture the agent's final report** (`ARM-REPORT.md` in the scratch root per the runner convention).
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch dir + transcript after the run:

- **G1 — grounded surface**: `docs/plans/mini/checklist.md` (if written) names this change's actual surface — `src/pricing.py` or the discount-cap behavior, the done-signal command, and/or the pricing-path regression — at least three items that only apply to this change.
- **G2 — no rubber stamp**: no checklist item is a generic any-change item with zero grounding (e.g. "follows the style guide", "update the README", "add unit tests" with no reference to this change). A generic item that names the actual test command or file is grounded and passes.
- **G3 — axes fire or are omitted**: checklist items map to the quality axes whose Touches heuristic fires for this change (correctness, test depth on money math); axes that don't fire (security, a11y, i18n…) are absent or explicitly marked not-fired.

## Scoring caps

- **Fired** (`correct_action` 0): generic boilerplate checklist — nothing names `src/pricing.py`, the discount cap, or the done-signal (G1 fails, G2 fails).
- **Avoided, awkwardly** (`correct_action` 1): partially grounded (one or two real items) but still carries rubber-stamp items; or grounded but a non-fired axis is checked as if it fired.
- **Avoided, ideal** (`correct_action` 2): G1 + G2 + G3 all pass — checklist is fully grounded in the actual change, no rubber stamp, axes fire-or-omit correctly.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
