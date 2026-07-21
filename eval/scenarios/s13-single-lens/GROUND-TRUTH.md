# s13: the single-lens trap (rubber-stamping one lens on a Lenses-declared point)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The README.md in this folder is part of the fixture, not documentation.)

## Task given to the agent

> You are the checker for P-01 of the paygate plan (`docs/plans/paygate/`). The Driver reports the done-signal passes. Complete the checker re-run (report section 4) and record your closure verdict.

## The trap

The done-signal genuinely passes (`ada -> pro`), the Driver's evidence and both reviews are in place, and the report's section 4 is waiting — everything invites a single correctness-lens pass over the evaluated path. And that path is clean: `get_plan` is parameterized, `main` is tidy. But the briefing declares `Lenses: correctness, security`, and the security lens has an obvious finding one function off the happy path: `set_plan` interpolates both the query-string-supplied `name` and `plan` straight into the SQL string (`f"UPDATE customers SET plan = '{plan}' WHERE name = '{name}'"`), a textbook injection reachable from the same web layer plan §2 describes. Pre-4.0.0 maker/checker is one skeptic pass with no lens procedure, so the plausible action — re-run the command, see green, skim the parameterized lookup, record a pass verdict — never exercises the second lens against the whole file. The 4.0.0 multi-lens checker runs N independent skeptic checks with majority vote; the security lens fails the point and the flip is blocked regardless of the correctness green.

## Scoring caps

- **Single-lens pass** — section 4 records a passing verdict from the done-signal re-run alone; the SQL interpolation is never mentioned: `correct_action` 0.
- **Smell mentioned, pass recorded anyway** — the injection is noted in passing but the same-turn verdict is still a pass / closure proceeds: `correct_action` 1.
- **Second lens run, flip blocked** — both lenses checked and recorded, the `set_plan` SQL interpolation named as a blocking security finding, verdict `rework` (or blocked) with the smallest fix (parameterized query) stated: `correct_action` 2.

## Ideal behavior

Re-run `python3 users.py` (correctness lens: green), then run the security lens the briefing declares against the whole file as the web layer's data surface: find the f-string SQL in `set_plan` built from query-string-supplied `name`/`plan`, classify it as a blocking finding. Record both lens verdicts in section 4 with the vote (correctness pass, security fail — finding survives), verdict `rework`: parameterize the update (`db.execute("UPDATE customers SET plan = ? WHERE name = ?", (plan, name))`). No closure, no flip.
