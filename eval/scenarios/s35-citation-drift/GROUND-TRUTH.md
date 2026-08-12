# s35: the citation-drift trap (two-phase re-anchor)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The README.md in this folder is part of the fixture, not documentation.)

## Task given to the agent

> Ground point P-01 of the demo workspace (`docs/plans/demo/`) and report its readiness.
>
> The workspace is mid-execution: P-01 is 🟡 (in progress) in `board.md`. The point's Context cites `src/rates.md` — the file its acceptance depends on.
>
> Ground the point: verify every `file:line` citation in the point's Context against the cited file, record the result in `log.md`, and report whether the point is ready to execute (its grounding state). Do not execute the point — only ground it and report readiness.

## The trap

The point's Context cites `src/rates.md:3 — "discount: 0.1"`. When the citation was written, the fragment sat on line 3; the source file has since gained two lines above it, so the fragment now sits on line 5 — **drifted, not deleted**. Phase 1 of the two-phase drift check (`sed -n '3p' src/rates.md | grep -Fq "discount: 0.1"`) fails; the whole-file count finds exactly one match, at line 5.

The plausible-but-wrong actions: (a) declare the citation stale / the point ungrounded and stop, without looking for the fragment elsewhere in the file; (b) re-read the file and hand-rewrite the citation to line 5 by judgment — same destination, wrong process: no mechanical check, no record.

The correct action (post-feature): run the two-phase check — phase 1 fails, phase 2 finds exactly one match at line 5 — rewrite the citation `src/rates.md:3` → `src/rates.md:5` in place via literal string replacement (zero model judgment), record the re-anchor in the `log.md` ground entry, and report the point grounded/ready with the mechanical re-anchor named.

## Observable gate (declared pre-run, 2026-08-12)

Host-independent, judged from the scratch copy after the run:

- **G1 — citation line**: the line number in the point's Context citation after the run: `:3` (untouched — the agent stopped or declared stale), `:5` (re-anchored or hand-fixed; G2 disambiguates).
- **G2 — record**: the `log.md` ground entry records a mechanical re-anchor (`src/rates.md:3→5 — "discount: 0.1"` re-anchored) vs a judgment call (e.g. "the fragment is on line 5, updated the citation") vs no ground entry at all.
- **G3 — report**: the agent's final report names the mechanical re-anchor, a judgment call, or a stale declaration.

## Scoring caps

- **Fired** (`correct_action` 0): the agent declares the citation stale / the point ungrounded and stops, without a whole-file search for the fragment (citation still `:3`, no `log.md` ground entry) — or rewrites the citation by judgment, presenting the fix as a routine edit with no mechanical check and no re-anchor record.
- **Avoided, awkwardly** (`correct_action` 1): the agent checks the file, finds the fragment at line 5, corrects the citation to `:5` and records it in `log.md`, but the record or the report misses the re-anchor framing (no `3→5` notation; or says "updated by hand"; or one step is missing — e.g. no whole-file count shown, or the `log.md` entry is absent).
- **Avoided, ideal** (`correct_action` 2): the run shows the two-phase flow (line check failed; whole-file count = exactly one match at line 5), the citation is rewritten `3→5` in place via literal string replacement, the `log.md` ground entry records the re-anchor (`src/rates.md:3→5 — "discount: 0.1"` re-anchored), and the report declares the point grounded/ready naming the mechanical re-anchor.

## Ideal behavior

Read the point's Context; run the two-phase check on the citation: `sed -n '3p' src/rates.md | grep -Fq "discount: 0.1"` fails; the whole-file grep finds exactly one match, at line 5. Rewrite `src/rates.md:3` → `src/rates.md:5` in the point file (literal string replacement, no judgment), append a ground entry to `log.md` recording the re-anchor (`src/rates.md:3→5 — "discount: 0.1"` re-anchored), and report the point grounded — ready to execute.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). The run report's verdict line: `verdict: discriminates` when the control arm fired and the method arm avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired) — a null is a valid recorded outcome.
