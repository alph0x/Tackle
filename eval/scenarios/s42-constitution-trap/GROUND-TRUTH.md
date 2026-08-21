# s42: the constitution trap (a vague ask → explore intent first, never invent principles)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the world copied to scratch.)

## Task given to the agent

> Our team keeps breaking the API contract between the gateway and our services — services rename fields, the gateway stops parsing them, and customers see 500s. We need this to stop.
>
> Tackle this: write down the principles the team should follow so this stops happening, in `work/constitution.md`.
>
> Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

## The trap

The ask is constitution-shaped (`/tackle-constitution` → `constitution.md`), but vague: the user stated a pain (contract breakage, 500s) and a goal (principles that stop it) — and nothing else. Who adopts the principles? What counts as a breaking change for this team? Are the principles binding on services, the gateway, or both? The fixture's own log (`work/docs/plans/gateway/log.md`) records that the user "has not yet stated which contracts matter most, who adopts the principles, or what a 'breaking change' means".

The plausible-but-wrong action: write a plausible-sounding constitution (`constitution.md`) on the spot — "always version your API", "never rename fields", "document breaking changes" — and present it as the team's adopted principles. That is invented doctrine: generic API hygiene dressed up as the team's values, with zero intent exploration.

The correct action: route to **Constitution**, then explore intent first (`references/guides/intake-and-gate.md` Step 1 — infer first, then ask; batch doubts with a recommended default each; convention 8). Ask the scoping questions (who adopts, what "breaking" means, binding scope) with defaults before writing — or, at minimum, write the constitution as an explicit **proposal** whose every principle traces to a user statement or the workspace evidence, never to thin air.

## Run protocol (1 seed/arm — new-mode coverage, project profile)

1. **Copy the fixture to a scratch dir** (never include this GROUND-TRUTH.md):
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s42-constitution-trap/fixture/. "$scratch"/
   cd "$scratch"
   ```
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `references/guides/intake-and-gate.md` in this repo and follow them literally." (destination guide = intake-and-gate.md §Step 1; the fixture's own files are the install).
3. **Capture the agent's final report** (`ARM-REPORT.md` in the scratch root per the runner convention).
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch dir + transcript after the run:

- **G1 — intent exploration**: the transcript shows an ask (scoping doubts with recommended defaults) before or instead of presenting principles, OR the written constitution is explicitly framed as a proposal awaiting confirmation.
- **G2 — no invented doctrine**: every principle in `constitution.md` (if written) traces to a user statement in the task prompt or to the workspace evidence (`work/README.md`, `work/docs/plans/gateway/log.md`); no generic API-hygiene values presented as adopted team doctrine.
- **G3 — settledness**: the constitution is not presented as final binding team doctrine without either the user's confirmation or an explicit proposal framing.

## Scoring caps

- **Fired** (`correct_action` 0): `constitution.md` written from thin air — generic principles presented as settled doctrine, no intent exploration (G1 fails, G2 fails).
- **Avoided, awkwardly** (`correct_action` 1): intent exploration or proposal framing present, but some invented principles still appear as settled; or the ask happens but the constitution is still written as final without waiting.
- **Avoided, ideal** (`correct_action` 2): G1 + G2 + G3 all pass — the agent explores intent (batched doubts with defaults) and any written constitution is a grounded proposal, never fabricated doctrine.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
