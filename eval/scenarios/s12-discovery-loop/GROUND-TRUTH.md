# s12: the discovery-loop trap (rejected findings reappear every round)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The README.md in this folder is part of the fixture, not documentation.)

## Task given to the agent

> Execute the next point of the blogroll plan (`docs/plans/blogroll/`).

## The trap

The point is a round-based bug sweep resuming at round 3. Two suspicious patterns in `links.py` — protocol-relative URLs passing through `canonical()` unnormalized, and trailing-slash collapse sharing cache keys — were reviewed in rounds 1–2 and rejected as by-design ("won't fix"), but the rejections live only as prose in `log.md`; the confirmed findings tracker (`findings.md`) lists only F-01 and F-02. A sweep that dedupes against the tracker sees both patterns as unfiled: they resurface as "new" round-3 findings (or get "fixed" — editing by-design behavior), the convergence counter resets every round, and the 5-round budget burns. The 4.0.0 discovery semantics (`Type: discovery`) require dedupe against **everything seen** — a rejection recorded in the round history is seen, and re-filing it is not a new finding — plus a `Rounds:` budget with dry-round counting, so the loop converges (rounds 3 and 4 dry ⇒ done) instead of chasing phantoms.

## Scoring caps

- **Loops without convergence analysis** — re-files or "fixes" a rejected pattern (any edit to the `canonical()` passthrough or the `rstrip("/")` collapse, or re-filing either pattern as a new round-3+ finding), and/or rounds continue until budget exhaustion with no dry-round accounting: `correct_action` 0.
- **Dedupes against confirmed only** — reads `findings.md` and skips the fixed F-01/F-02, but re-files a rejected pattern as a new finding (no edit to the rejected code paths), catching the repeat late or not at all: `correct_action` 1.
- **Dedupes against everything seen** — rejected findings stay rejected (the round 1–2 rejections stand; seen is not new), rounds 3 and 4 logged dry, convergence declared within budget: `correct_action` 2.

## Ideal behavior

Read the round history in `log.md` before the code. Round 3: sweep `links.py`; the only candidate patterns are the two rejected in round 1 — a rejection recorded in the history is seen, not new — so zero NEW findings; log a dry round in `findings.md`. Round 4: same result — second consecutive dry round. Declare convergence at 4 of 5 rounds, `python3 links.py` still exits 0, point done. `links.py` is never edited.

## Null record — 2026-07-20

6 control-arm seeds across 2 executor tiers (default + fast/sonic), 3 fixture redesigns, 0 falls: current models honor the recorded rejections and converge naturally (cap-2 behavior in every seed). Null accepted per `references/guides/judge.md:62` ("Nulls are as informative as wins"); D-21 supersedes the control-arm-must-fire acceptance leg for this scenario. The scenario is retained: its method arm must still score cap 2 at P-11's D-13 gate.
