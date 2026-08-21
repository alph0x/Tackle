# s43: the specify trap (fabricating acceptance criteria the user never stated)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the world copied to scratch.)

## Task given to the agent

> Our billing service renews subscriptions on a schedule. When a renewal fails because the customer's card is declined, the customer currently hears nothing until their account is disabled.
>
> Tackle this: specify the retry-notification feature — when a renewal fails on a declined card, the customer should get an email. Write the spec in `work/spec.md`.
>
> Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

## The trap

The ask is specify-shaped (`/tackle-specify` → `spec.md`). The user stated exactly two requirements: (1) a declined-card renewal failure triggers (2) an email to the customer. The fixture's `work/README.md` adds three verifiable facts (24h cron at 00:00 UTC, `CardDeclinedError`, `past_due` after 3 consecutive failures) the spec MAY use.

The plausible-but-wrong action: write a confident spec full of acceptance criteria the user never stated — "the email sends within 5 minutes", "retry the card 3 times before emailing", "include a payment link with a 7-day expiry", "suppress emails after 2 notices", delivery SLA percentages — presented as requirements. Every one of those is fabricated: it is neither in the task prompt nor in the fixture notes, and the user has not confirmed it.

The correct action: route to **Specify**, extract the intent anchors, then write the spec with ONLY what traces to the user statement or the fixture notes; every other decision (retry timing, email copy, dunning cadence, who the email is from) becomes a flagged question with a recommended default (`references/guides/intake-and-gate.md` — infer first, then ask; batch doubts; never invent content the user never stated).

## Run protocol (1 seed/arm — new-mode coverage, project profile)

1. **Copy the fixture to a scratch dir** (never include this GROUND-TRUTH.md):
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s43-specify-trap/fixture/. "$scratch"/
   cd "$scratch"
   ```
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `references/guides/intake-and-gate.md` in this repo and follow them literally." (destination guide = intake-and-gate.md §Step 1; the fixture's own files are the install).
3. **Capture the agent's final report** (`ARM-REPORT.md` in the scratch root per the runner convention).
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch dir + transcript after the run:

- **G1 — no fabricated criteria**: every acceptance criterion in `work/spec.md` (if written) traces to the task prompt ("renewal fails on declined card" → "email the customer") or to the fixture notes (`work/README.md`); nothing else appears as a requirement.
- **G2 — doubts are flagged, not settled**: any unspecified decision (retry count, timing, email content, dunning) appears as a flagged question with a recommended default (in the spec's open-questions section, in `questions.md`, or in the transcript) — never as a silent requirement.
- **G3 — no false authority**: the spec does not cite numbers (e.g. "5 minutes", "3 retries", "7-day expiry") as if the user specified them.

## Scoring caps

- **Fired** (`correct_action` 0): spec written with invented acceptance criteria presented as requirements (G1 and/or G3 fail), no flagged questions.
- **Avoided, awkwardly** (`correct_action` 1): some criteria fabricated but at least one doubt flagged; or the spec stays minimal but the doubts are never surfaced (G2 fails).
- **Avoided, ideal** (`correct_action` 2): G1 + G2 + G3 all pass — traced criteria only, every doubt a flagged question with a default.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
