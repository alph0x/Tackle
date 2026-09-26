# Second candidate cohort: the 9.0.0 candidate against the 8.4.1 method

Development-grade evidence. Each episode ran as a Claude Code subagent of the coordinating session, on the operator's machine and login, not in an isolated install: it started in the host repository, and every arm could reach the installed skill and that repository. The contamination audit sees only what the transcript's tool calls name; an episode it flags is invalid and leaves the counts. The method and method:candidate arms are asked to read and follow their staged skill, as a user who invokes it would; triggering is not measured. The method:split arm runs only in the smoke: its planner session is asked to write a paper plan instead of running the skill's own PLAN scaffolding, a disclosed fidelity simplification, and both of its sessions are pinned to the cheapest bindable tier. The pilot runs no split episodes, because planning on a more capable tier than execution is now a rule of the candidate. At three seeds per arm per variant, protocol v2's own native per-variant labels (`discriminates`, `method-worse`) are mathematically unreachable: the single most extreme 3-vs-3 split lands exactly at the significance threshold, not below it, so those lines below can only ever read `unobserved`, `inert`, `inconclusive` or `contaminated` here. The `pooled[...]` lines below are protocol v2's own native pooling across all three outcome-trap variants; the Decision section's own pooled figure is a separate computation over only the two pre-registered primary variants, excluding the held-out tripwire variant, which is pooled only as a binary trap there instead — the real evidentiary lift comes from that pooled bound and tripwire, never from the native per-variant labels. The held-out third variant is a binary tripwire on the candidate comparison, never pooled into either arm's own primary figure. Two disclosed mechanism episodes carry pinned, coordinator-supplied sentences overriding their ordinary instructions, to prove the tool's own three-session merge and escalation mechanism live. The smoke cohort's first attempt is recorded invalid: its planner wrote the escalation line in its reply instead of in the brief, whose file the pinned sentence did not name. The smoke-2 cohort's retry, whose sentence names the brief file, completed all three sessions. Neither is pooled into, or read as, a behavioral measurement of planning quality. One pilot episode is recorded as an error: the coordinator read its transcript before the session had finished, and that episode's judged outcome is never used. The price table's fresh-input pricing of a blended tokens_in is a disclosed, conservative approximation, not a precise dollar figure.

Hypothesis: With the Tackle 9.0.0 candidate, a Haiku executor falls into the planning-outcome traps no more often than with the 8.4.1 method, replicated at three seeds per held-out variant.

Arms: `method` receives the 8.4.1 install; `method:candidate` receives the 9.0.0 candidate as a fixed, single session at the cheapest tier. In the smoke only, `method:split` receives the 9.0.0 candidate as a planner session then an executor session, both pinned to the cheapest tier, to prove the multi-session mechanism; the pilot runs no split episodes, so the Decision section's split line has no split-arm figures; the routing default is settled by the candidate's own rule, not by that line.

## Pilot: held-out variants

- Cohort `2026-09-second-candidate`, seal `961afd84a38268989e918a1ce38b1ae4d4817c67db3c4cd1de4ab3e8dbf8b8ba`, created 2026-09-26T22:20:03Z.
- Variants: `s62-caller-contract/h1` (held-out), `s63-documented-edge-rule/h1` (held-out), `s64-stored-data-compat/h1` (held-out).
- Executor: claude-code-subagent, `claude-haiku-4-5`; as served: `claude-haiku-4-5-20251001`. Judge: mechanical hidden acceptance tests, blinded.
- Artifacts: candidate `06c2fd84139648186146f51c8f231504fa64e930dcbe11da7f81fddf0e079774`; method (8.4.1) `239ceb22fe0cc842393a7e0430b8dd8c0924139b2f64cd17261ffbb6ee041abe`.

```text
verdict[candidate] s62-caller-contract/h1 inconclusive method 2/2 [0.3424,1.0000] method:candidate 3/3 [0.4385,1.0000] p_better=1.0000 p_worse=1.0000
verdict[candidate] s63-documented-edge-rule/h1 inert method 0/3 [0.0000,0.5615] method:candidate 0/3 [0.0000,0.5615] p_better=1.0000 p_worse=1.0000
verdict[candidate] s64-stored-data-compat/h1 inconclusive method 1/3 [0.0615,0.7923] method:candidate 1/3 [0.0615,0.7923] p_better=0.8000 p_worse=0.8000
pooled[candidate] 0.0000 [0.0000,0.0000] seed=20260923 B=10000
```

| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | Files written | Check runs | Correction cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pilot-1 | s63-documented-edge-rule/h1 | method:candidate | avoided | clean | 705383 | 5106 | 62 | 13 | 4 | 4 | 2 |
| pilot-2 | s64-stored-data-compat/h1 | method:candidate | avoided | clean | 658975 | 5872 | 67 | 12 | 4 | 2 | 0 |
| pilot-3 | s63-documented-edge-rule/h1 | method:candidate | avoided | clean | 708599 | 4042 | 62 | 13 | 4 | 4 | 2 |
| pilot-4 | s62-caller-contract/h1 | method | error | clean | 644745 | 2774 | 43 | 13 | 6 | 4 | 2 |
| pilot-5 | s62-caller-contract/h1 | method:candidate | fell | clean | 984133 | 5841 | 77 | 18 | 6 | 5 | 2 |
| pilot-6 | s63-documented-edge-rule/h1 | method | avoided | clean | 663490 | 4931 | 60 | 12 | 4 | 2 | 1 |
| pilot-7 | s62-caller-contract/h1 | method | fell | clean | 912507 | 6199 | 80 | 17 | 6 | 5 | 2 |
| pilot-8 | s62-caller-contract/h1 | method:candidate | fell | clean | 1179711 | 7428 | 112 | 21 | 10 | 4 | 2 |
| pilot-9 | s64-stored-data-compat/h1 | method | avoided | clean | 942880 | 8332 | 90 | 17 | 5 | 4 | 0 |
| pilot-10 | s62-caller-contract/h1 | method:candidate | fell | clean | 1057809 | 5141 | 82 | 19 | 6 | 4 | 2 |
| pilot-11 | s63-documented-edge-rule/h1 | method | avoided | clean | 771441 | 5874 | 70 | 14 | 4 | 4 | 2 |
| pilot-12 | s64-stored-data-compat/h1 | method:candidate | fell | clean | 769839 | 6745 | 73 | 14 | 5 | 1 | 0 |
| pilot-13 | s64-stored-data-compat/h1 | method | fell | clean | 868690 | 5566 | 75 | 16 | 4 | 2 | 0 |
| pilot-14 | s64-stored-data-compat/h1 | method | avoided | clean | 816842 | 5709 | 70 | 15 | 4 | 2 | 0 |
| pilot-15 | s62-caller-contract/h1 | method | fell | clean | 811394 | 5445 | 69 | 15 | 6 | 4 | 2 |
| pilot-16 | s63-documented-edge-rule/h1 | method:candidate | avoided | clean | 1085974 | 7813 | 111 | 19 | 8 | 4 | 2 |
| pilot-17 | s64-stored-data-compat/h1 | method:candidate | avoided | clean | 1264524 | 7286 | 115 | 23 | 5 | 4 | 0 |
| pilot-18 | s63-documented-edge-rule/h1 | method | avoided | clean | 825794 | 5799 | 85 | 15 | 4 | 3 | 1 |

| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |
|---|---|---|---|---|---|---|---|---|
| method | 9 | 8 | 3 | 7257783 | 50629 | 642 | 134 | 10 |
| method:candidate | 9 | 9 | 4 | 8414947 | 55274 | 761 | 152 | 12 |

Roles and per-episode dollar cost:

| Episode | Arm | Role | Tier | Model | Tokens in | Tokens out | Episode $ |
|---|---|---|---|---|---|---|---|
| pilot-1 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 705383 | 5106 | 0.7309 |
| pilot-2 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 658975 | 5872 | 0.6883 |
| pilot-3 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 708599 | 4042 | 0.7288 |
| pilot-4 | method | n/a | n/a | claude-haiku-4-5-20251001 | 644745 | 2774 | 0.6586 |
| pilot-5 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 984133 | 5841 | 1.0133 |
| pilot-6 | method | n/a | n/a | claude-haiku-4-5-20251001 | 663490 | 4931 | 0.6881 |
| pilot-7 | method | n/a | n/a | claude-haiku-4-5-20251001 | 912507 | 6199 | 0.9435 |
| pilot-8 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 1179711 | 7428 | 1.2169 |
| pilot-9 | method | n/a | n/a | claude-haiku-4-5-20251001 | 942880 | 8332 | 0.9845 |
| pilot-10 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 1057809 | 5141 | 1.0835 |
| pilot-11 | method | n/a | n/a | claude-haiku-4-5-20251001 | 771441 | 5874 | 0.8008 |
| pilot-12 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 769839 | 6745 | 0.8036 |
| pilot-13 | method | n/a | n/a | claude-haiku-4-5-20251001 | 868690 | 5566 | 0.8965 |
| pilot-14 | method | n/a | n/a | claude-haiku-4-5-20251001 | 816842 | 5709 | 0.8454 |
| pilot-15 | method | n/a | n/a | claude-haiku-4-5-20251001 | 811394 | 5445 | 0.8386 |
| pilot-16 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 1085974 | 7813 | 1.1250 |
| pilot-17 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 1264524 | 7286 | 1.3010 |
| pilot-18 | method | n/a | n/a | claude-haiku-4-5-20251001 | 825794 | 5799 | 0.8548 |

Audit:

- Clean: 18 of 18.

Escalation mechanism episode, post-hoc model check: **not observed** (roles' models in order: n/a).

## Smoke: smoke

- Cohort `2026-09-second-candidate-smoke`, seal `0631e91ac0f2313622c431a54085ad06e8f06048592555b8704f1063a69b9414`, created 2026-09-26T22:20:03Z.
- Variants: `s62-caller-contract/v1` (development).
- Executor: claude-code-subagent, `claude-haiku-4-5`; as served: `claude-haiku-4-5-20251001`. Judge: mechanical hidden acceptance tests, blinded.
- Artifacts: candidate `06c2fd84139648186146f51c8f231504fa64e930dcbe11da7f81fddf0e079774`; method (8.4.1) `n/a`.

```text

```

| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | Files written | Check runs | Correction cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smoke-mechanism | s62-caller-contract/v1 | method:split | invalid | invalid | 828742 | 6648 | 88 | 13 | 0 | 0 | 0 |
| smoke-plain | s62-caller-contract/v1 | method:split | fell | clean | 1314085 | 8164 | 111 | 22 | 5 | 3 | 2 |

| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |
|---|---|---|---|---|---|---|---|---|
| method:split | 2 | 1 | 1 | 2142827 | 14812 | 199 | 35 | 2 |

Roles and per-episode dollar cost:

| Episode | Arm | Role | Tier | Model | Tokens in | Tokens out | Episode $ |
|---|---|---|---|---|---|---|---|
| smoke-mechanism | method:split | planner | fast | claude-haiku-4-5-20251001 | 613840 | 5567 | 0.8620 |
| smoke-mechanism | method:split | executor | fast | claude-haiku-4-5-20251001 | 214902 | 1081 | 0.8620 |
| smoke-plain | method:split | planner | fast | claude-haiku-4-5-20251001 | 771668 | 4533 | 1.3549 |
| smoke-plain | method:split | executor | fast | claude-haiku-4-5-20251001 | 542417 | 3631 | 1.3549 |

Audit:

- Clean: 1 of 2.
- smoke-mechanism: escalation without a declared brief (0 outside path(s), skill used: False).

Escalation mechanism episode, post-hoc model check: **not observed** (roles' models in order: n/a).

## Smoke: smoke-2

- Cohort `2026-09-second-candidate-smoke-2`, seal `509108549b7875f968cb4d3b5915899879582dd84a04700bb0a425c1e0306752`, created 2026-09-26T22:28:08Z.
- Variants: `s62-caller-contract/v1` (development).
- Executor: claude-code-subagent, `claude-haiku-4-5`; as served: `claude-haiku-4-5-20251001`. Judge: mechanical hidden acceptance tests, blinded.
- Artifacts: candidate `06c2fd84139648186146f51c8f231504fa64e930dcbe11da7f81fddf0e079774`; method (8.4.1) `n/a`.

```text

```

| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | Files written | Check runs | Correction cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smoke2-mechanism | s62-caller-contract/v1 | method:split | avoided | clean | 2519048 | 17933 | 270 | 36 | 9 | 2 | 0 |

| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |
|---|---|---|---|---|---|---|---|---|
| method:split | 1 | 1 | 0 | 2519048 | 17933 | 270 | 36 | 0 |

Roles and per-episode dollar cost:

| Episode | Arm | Role | Tier | Model | Tokens in | Tokens out | Episode $ |
|---|---|---|---|---|---|---|---|
| smoke2-mechanism | method:split | planner | fast | claude-haiku-4-5-20251001 | 783731 | 5159 | 4.1872 |
| smoke2-mechanism | method:split | executor | fast | claude-haiku-4-5-20251001 | 214500 | 1235 | 4.1872 |
| smoke2-mechanism | method:split | executor | standard | claude-sonnet-5 | 1520817 | 11539 | 4.1872 |

Audit:

- Clean: 1 of 1.

Escalation mechanism episode, post-hoc model check: **pass** (roles' models in order: claude-haiku-4-5, claude-haiku-4-5, claude-sonnet-5).

## Decision

- `candidate`: **FAIL** (median tokens_in is not strictly lower for method:candidate)
- `split`: report-only: pooled figure not computed (fewer than 2 valid episodes for at least one arm/variant); tripwire clear; median episode cost method:candidate=$1.0484 method:split=n/a; a two-session planning pass at a fixed cheap tier is evidence toward the routing default's wording, never a gate, at this sample size
