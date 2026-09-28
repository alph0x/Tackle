# Third candidate cohort: the 9.0.0 candidate that runs only current workspaces, against the 8.4.1 method

Development-grade evidence. Each episode ran as a Claude Code subagent of the coordinating session, on the operator's machine and login, not in an isolated install: it started in the host repository, and every arm could reach the installed skill and that repository. The contamination audit sees only what the transcript's tool calls name; an episode it flags is invalid and leaves the counts. The method and method:candidate arms are asked to read and follow their staged skill, as a user who invokes it would; triggering is not measured. Every episode, smoke and pilot, is one session at the cheapest tier. At three seeds per arm per variant, protocol v2's own native per-variant labels (`discriminates`, `method-worse`) are mathematically unreachable: the single most extreme 3-vs-3 split lands exactly at the significance threshold, not below it, so those lines below can only ever read `unobserved`, `inert`, `inconclusive` or `contaminated` here. The `pooled[candidate]` line pools the outcome-trap variants that are neither contaminated nor unobserved. It bootstraps variant-level differences, so with three variants its interval runs from the smallest to the largest difference, and all-zero differences print [0.0000,0.0000], a degenerate interval, not a tight estimate. The Decision section pools only the two primary variants; with two, its lower bound is the smaller difference, a screen for an observed regression, not a significance test. The held-out third variant is a binary tripwire on both decision lines, never pooled into either arm's own primary figure. The smoke's two episodes run on a development variant to check staging and the close chain; they are pooled into nothing and read as no measurement. The fresh-input column prices every input token at the fresh rate, though most input is cache reads, and overstates spend; it is disclosure only. The cache-aware column prices each episode's own transcript usage, cache writes and reads included, at published rates, and is the spend. These traps start in a fresh fixture repository with no workspace, so neither line measures how the candidate treats an older workspace.

Hypothesis: With the Tackle 9.0.0 candidate, which runs only current workspaces, a Haiku executor falls into the planning-outcome traps no more often than with the 8.4.1 method, replicated at three seeds per held-out variant.

Arms: `method` receives the 8.4.1 install; `method:candidate` receives the 9.0.0 candidate as a fixed, single session at the cheapest tier. The smoke runs one episode of each arm on a development variant, to check that both installs stage and that the close chain records them; it gates nothing.

## Pilot: held-out variants

- Cohort `2026-09-third-candidate`, seal `d470ee79993e22f417078f96b5269c3fda373b8379b12820e1bca32f4de53640`, created 2026-09-28T14:01:42Z.
- Variants: `s62-caller-contract/h1` (held-out), `s63-documented-edge-rule/h1` (held-out), `s64-stored-data-compat/h1` (held-out).
- Executor: claude-code-subagent, `claude-haiku-4-5`; as served: `claude-haiku-4-5-20251001`. Judge: mechanical hidden acceptance tests, blinded.
- Artifacts: baseline (method, 8.4.1) `239ceb22fe0cc842393a7e0430b8dd8c0924139b2f64cd17261ffbb6ee041abe` and candidate `1d2b48c658eee4c4719c8e0aa5f3eb13d33fc48cc33a29ce229161721523f674`, from the manifest; every record's artifact_sha256 matches its arm's: yes.

```text
verdict[candidate] s62-caller-contract/h1 inconclusive method 3/3 [0.4385,1.0000] method:candidate 3/3 [0.4385,1.0000] p_better=1.0000 p_worse=1.0000
verdict[candidate] s63-documented-edge-rule/h1 inert method 0/3 [0.0000,0.5615] method:candidate 0/3 [0.0000,0.5615] p_better=1.0000 p_worse=1.0000
verdict[candidate] s64-stored-data-compat/h1 inconclusive method 3/3 [0.4385,1.0000] method:candidate 1/3 [0.0615,0.7923] p_better=0.2000 p_worse=1.0000
pooled[candidate] 0.2222 [0.0000,0.6667] seed=20260923 B=10000
```

The `pooled[candidate]` line pools the outcome-trap variants that are neither contaminated nor unobserved. It bootstraps variant-level differences, so with three variants its interval runs from the smallest to the largest difference, and all-zero differences print [0.0000,0.0000], a degenerate interval, not a tight estimate. The Decision section pools only the two primary variants; with two, its lower bound is the smaller difference, a screen for an observed regression, not a significance test.

| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | Files written | Check runs | Correction cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pilot-1 | s63-documented-edge-rule/h1 | method | avoided | clean | 866698 | 5646 | 70 | 16 | 4 | 4 | 2 |
| pilot-2 | s62-caller-contract/h1 | method | fell | clean | 865891 | 5851 | 74 | 16 | 6 | 5 | 2 |
| pilot-3 | s64-stored-data-compat/h1 | method | fell | clean | 816103 | 5211 | 70 | 15 | 4 | 3 | 0 |
| pilot-4 | s63-documented-edge-rule/h1 | method:candidate | avoided | clean | 821707 | 5621 | 62 | 15 | 4 | 2 | 1 |
| pilot-5 | s64-stored-data-compat/h1 | method:candidate | fell | clean | 1246414 | 9956 | 123 | 22 | 9 | 1 | 0 |
| pilot-6 | s62-caller-contract/h1 | method | fell | clean | 964683 | 5331 | 73 | 18 | 6 | 5 | 1 |
| pilot-7 | s62-caller-contract/h1 | method:candidate | fell | clean | 802535 | 4701 | 62 | 15 | 6 | 4 | 2 |
| pilot-8 | s63-documented-edge-rule/h1 | method:candidate | avoided | clean | 706007 | 4843 | 68 | 13 | 4 | 4 | 2 |
| pilot-9 | s64-stored-data-compat/h1 | method | fell | clean | 834269 | 6891 | 97 | 15 | 4 | 4 | 2 |
| pilot-10 | s63-documented-edge-rule/h1 | method:candidate | avoided | clean | 888394 | 6207 | 71 | 16 | 5 | 3 | 2 |
| pilot-11 | s62-caller-contract/h1 | method:candidate | fell | clean | 1019735 | 7081 | 86 | 19 | 6 | 5 | 2 |
| pilot-12 | s63-documented-edge-rule/h1 | method | avoided | clean | 716773 | 5426 | 67 | 13 | 4 | 4 | 2 |
| pilot-13 | s64-stored-data-compat/h1 | method | fell | clean | 718936 | 5095 | 61 | 13 | 4 | 2 | 0 |
| pilot-14 | s64-stored-data-compat/h1 | method:candidate | avoided | clean | 768755 | 6415 | 73 | 14 | 4 | 2 | 0 |
| pilot-15 | s62-caller-contract/h1 | method:candidate | fell | clean | 799805 | 4602 | 61 | 15 | 6 | 5 | 2 |
| pilot-16 | s62-caller-contract/h1 | method | fell | clean | 754791 | 4646 | 62 | 14 | 6 | 4 | 2 |
| pilot-17 | s63-documented-edge-rule/h1 | method | avoided | clean | 925054 | 5926 | 73 | 17 | 4 | 4 | 1 |
| pilot-18 | s64-stored-data-compat/h1 | method:candidate | avoided | clean | 712098 | 5391 | 61 | 13 | 4 | 2 | 0 |

Not counted: none.

| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |
|---|---|---|---|---|---|---|---|---|
| method | 9 | 9 | 6 | 7463198 | 50023 | 647 | 137 | 12 |
| method:candidate | 9 | 9 | 4 | 7765450 | 54817 | 667 | 142 | 11 |

Per-episode dollars:

| Episode | Arm | Model | Tokens in | Tokens out | Fresh-input $ | Cache-aware $ |
|---|---|---|---|---|---|---|
| pilot-1 | method | claude-haiku-4-5-20251001 | 866698 | 5646 | 0.8949 | 0.1431 |
| pilot-2 | method | claude-haiku-4-5-20251001 | 865891 | 5851 | 0.8951 | 0.1444 |
| pilot-3 | method | claude-haiku-4-5-20251001 | 816103 | 5211 | 0.8422 | 0.1359 |
| pilot-4 | method:candidate | claude-haiku-4-5-20251001 | 821707 | 5621 | 0.8498 | 0.1393 |
| pilot-5 | method:candidate | claude-haiku-4-5-20251001 | 1246414 | 9956 | 1.2962 | 0.2124 |
| pilot-6 | method | claude-haiku-4-5-20251001 | 964683 | 5331 | 0.9913 | 0.1515 |
| pilot-7 | method:candidate | claude-haiku-4-5-20251001 | 802535 | 4701 | 0.8260 | 0.1303 |
| pilot-8 | method:candidate | claude-haiku-4-5-20251001 | 706007 | 4843 | 0.7302 | 0.1217 |
| pilot-9 | method | claude-haiku-4-5-20251001 | 834269 | 6891 | 0.8687 | 0.1483 |
| pilot-10 | method:candidate | claude-haiku-4-5-20251001 | 888394 | 6207 | 0.9194 | 0.1505 |
| pilot-11 | method:candidate | claude-haiku-4-5-20251001 | 1019735 | 7081 | 1.0551 | 0.1679 |
| pilot-12 | method | claude-haiku-4-5-20251001 | 716773 | 5426 | 0.7439 | 0.1269 |
| pilot-13 | method | claude-haiku-4-5-20251001 | 718936 | 5095 | 0.7444 | 0.1252 |
| pilot-14 | method:candidate | claude-haiku-4-5-20251001 | 768755 | 6415 | 0.8008 | 0.1384 |
| pilot-15 | method:candidate | claude-haiku-4-5-20251001 | 799805 | 4602 | 0.8228 | 0.1293 |
| pilot-16 | method | claude-haiku-4-5-20251001 | 754791 | 4646 | 0.7780 | 0.1250 |
| pilot-17 | method | claude-haiku-4-5-20251001 | 925054 | 5926 | 0.9547 | 0.1514 |
| pilot-18 | method:candidate | claude-haiku-4-5-20251001 | 712098 | 5391 | 0.7391 | 0.1260 |
| Total | | | | | 15.7528 | 2.5675 |

Audit:

- Clean: 18 of 18.

## Smoke: smoke

- Cohort `2026-09-third-candidate-smoke`, seal `07ff6a3b07040c23a6d5d70481f3745594080548c10ec240e833745a5c360862`, created 2026-09-28T14:01:42Z.
- Variants: `s62-caller-contract/v1` (development).
- Executor: claude-code-subagent, `claude-haiku-4-5`; as served: `claude-haiku-4-5-20251001`. Judge: mechanical hidden acceptance tests, blinded.
- Artifacts: baseline (method, 8.4.1) `239ceb22fe0cc842393a7e0430b8dd8c0924139b2f64cd17261ffbb6ee041abe` and candidate `1d2b48c658eee4c4719c8e0aa5f3eb13d33fc48cc33a29ce229161721523f674`, from the manifest; every record's artifact_sha256 matches its arm's: yes.

(no comparison: development-grade smoke)

| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | Files written | Check runs | Correction cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smoke-candidate | s62-caller-contract/v1 | method:candidate | fell | clean | 1076916 | 7676 | 105 | 19 | 7 | 3 | 2 |
| smoke-method | s62-caller-contract/v1 | method | fell | clean | 702399 | 4423 | 57 | 13 | 4 | 3 | 2 |

Not counted: none.

| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |
|---|---|---|---|---|---|---|---|---|
| method | 1 | 1 | 1 | 702399 | 4423 | 57 | 13 | 2 |
| method:candidate | 1 | 1 | 1 | 1076916 | 7676 | 105 | 19 | 2 |

Per-episode dollars:

| Episode | Arm | Model | Tokens in | Tokens out | Fresh-input $ | Cache-aware $ |
|---|---|---|---|---|---|---|
| smoke-candidate | method:candidate | claude-haiku-4-5-20251001 | 1076916 | 7676 | 1.1153 | 0.2117 |
| smoke-method | method | claude-haiku-4-5-20251001 | 702399 | 4423 | 0.7245 | 0.1180 |
| Total | | | | | 1.8398 | 0.3297 |

Audit:

- Clean: 2 of 2.

## Decision

- `candidate`: **FAIL** (median tool_calls is not strictly lower for method:candidate)
- no-regression: PASS (the candidate's fall rate is not above the method's on either pooled variant, and the tripwire is clear); pooled fall-rate lower bound 0.0000; tripwire clear; a screen for an observed regression, not a significance test
