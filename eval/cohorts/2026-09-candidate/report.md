# Candidate cohort 2026-09: the 9.0.0 candidate against the 8.4.1 method and no skill

Development-grade evidence. Each episode ran as a Claude Code subagent of the coordinating session, on the operator's machine and login, not in an isolated install: it started in the host repository, and every arm could reach the installed skill and that repository. The contamination audit sees only what the transcript's tool calls name; an episode it flags is invalid and leaves the counts. The method and method:candidate arms are asked to read and follow their staged skill, as a user who invokes it would; triggering is not measured. The method:routed arm's planner session is asked to write a paper plan instead of running the skill's own PLAN scaffolding, a disclosed fidelity simplification. One seed per arm and variant (n_min 1) can reach only inert or inconclusive for a variant that is observed alone, so this report reads the pooled difference (over the two pre-registered primary variants only) and the costs, not a per-variant claim. The held-out third variant is a binary tripwire on every comparison, never pooled. For 9.0.0 there is no live third (escalated) session in any episode; that path is proven only by the tool's own unit tests, a disclosed gap. The routing comparison changes both the session split and the tier selected at once, so it cannot isolate which one helps; a fifth arm that would is a named, un-built future refinement. The price table's fresh-input pricing of a blended tokens_in is a disclosed, conservative approximation, not a precise dollar figure.

Hypothesis: With the Tackle 9.0.0 candidate, a Haiku executor falls into the planning-outcome traps no more often than with the 8.4.1 method; with the candidate's per-task routing engaged, no more often and at no higher cost than with the candidate at fixed tiers.

Arms: `control` receives the task alone; `method` receives the 8.4.1 install; `method:candidate` receives the 9.0.0 candidate at fixed tiers; `method:routed` receives the 9.0.0 candidate with per-task routing engaged (a frontier-tier planner, then an executor at the tier its brief compiles).

## Pilot: held-out variants

- Cohort `2026-09-candidate`, seal `bbf46a5feb5cac6a37238003ef33ae9ed20c09f6f375775b0d397c262ae5a5d1`, created 2026-09-26T12:14:12Z.
- Variants: `s62-caller-contract/h1` (held-out), `s63-documented-edge-rule/h1` (held-out), `s64-stored-data-compat/h1` (held-out).
- Executor: claude-code-subagent, `claude-haiku-4-5`; as served: `claude-haiku-4-5-20251001`, `claude-opus-5-5`. Judge: mechanical hidden acceptance tests, blinded.
- Artifacts: candidate (9.0.0) `6acd83167c803ad260a2348bd9f6bc32b9d3d26a01ab18591903a00fed1ff2bd`; method (8.4.1) `239ceb22fe0cc842393a7e0430b8dd8c0924139b2f64cd17261ffbb6ee041abe`.

```text
verdict s62-caller-contract/h1 inconclusive control 1/1 [0.2065,1.0000] method 1/1 [0.2065,1.0000] p_better=1.0000 p_worse=1.0000
verdict s63-documented-edge-rule/h1 inert control 0/1 [0.0000,0.7935] method 0/1 [0.0000,0.7935] p_better=1.0000 p_worse=1.0000
verdict s64-stored-data-compat/h1 inconclusive control 1/1 [0.2065,1.0000] method 1/1 [0.2065,1.0000] p_better=1.0000 p_worse=1.0000
verdict[candidate] s62-caller-contract/h1 inconclusive method 1/1 [0.2065,1.0000] method:candidate 1/1 [0.2065,1.0000] p_better=1.0000 p_worse=1.0000
verdict[candidate] s63-documented-edge-rule/h1 unobserved method 0/1 [0.0000,0.7935] method:candidate -/0 [n/a] p_better=n/a p_worse=n/a
verdict[candidate] s64-stored-data-compat/h1 inconclusive method 1/1 [0.2065,1.0000] method:candidate 0/1 [0.0000,0.7935] p_better=0.5000 p_worse=1.0000
pooled[candidate] 0.5000 [0.0000,1.0000] seed=20260923 B=10000
verdict[routing] s62-caller-contract/h1 inconclusive method:candidate 1/1 [0.2065,1.0000] method:routed 0/1 [0.0000,0.7935] p_better=0.5000 p_worse=1.0000
verdict[routing] s63-documented-edge-rule/h1 unobserved method:candidate -/0 [n/a] method:routed 0/1 [0.0000,0.7935] p_better=n/a p_worse=n/a
verdict[routing] s64-stored-data-compat/h1 inert method:candidate 0/1 [0.0000,0.7935] method:routed 0/1 [0.0000,0.7935] p_better=1.0000 p_worse=1.0000
pooled[routing] 0.5000 [0.0000,1.0000] seed=20260923 B=10000
pooled 0.0000 [0.0000,0.0000] seed=20260923 B=10000
```

| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | Files written | Check runs | Correction cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pilot-1 | s64-stored-data-compat/h1 | control | fell | clean | 536622 | 4401 | 54 | 10 | 4 | 3 | 2 |
| pilot-2 | s63-documented-edge-rule/h1 | control | avoided | clean | 585752 | 4492 | 54 | 11 | 4 | 3 | 2 |
| pilot-3 | s64-stored-data-compat/h1 | method:routed | avoided | clean | 5955104 | 140624 | 1624 | 59 | 3 | 4 | 1 |
| pilot-4 | s63-documented-edge-rule/h1 | method:routed | avoided | clean | 4160347 | 95696 | 1113 | 39 | 2 | 4 | 1 |
| pilot-5 | s63-documented-edge-rule/h1 | method:candidate | invalid | invalid | 708456 | 5942 | 69 | 13 | 4 | 4 | 2 |
| pilot-6 | s64-stored-data-compat/h1 | method | fell | clean | 711016 | 4663 | 59 | 13 | 4 | 4 | 2 |
| pilot-7 | s63-documented-edge-rule/h1 | method | avoided | clean | 766814 | 5589 | 68 | 14 | 4 | 4 | 2 |
| pilot-8 | s62-caller-contract/h1 | method:candidate | fell | clean | 856090 | 5116 | 66 | 16 | 6 | 5 | 2 |
| pilot-9 | s62-caller-contract/h1 | method:routed | avoided | clean | 10732664 | 161916 | 1912 | 75 | 4 | 4 | 0 |
| pilot-10 | s64-stored-data-compat/h1 | method:candidate | avoided | clean | 811847 | 5615 | 67 | 15 | 4 | 3 | 1 |
| pilot-11 | s62-caller-contract/h1 | control | fell | clean | 768307 | 3507 | 61 | 15 | 6 | 3 | 2 |
| pilot-12 | s62-caller-contract/h1 | method | fell | clean | 750780 | 3786 | 58 | 14 | 4 | 4 | 2 |

| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |
|---|---|---|---|---|---|---|---|---|
| control | 3 | 3 | 2 | 1890681 | 12400 | 169 | 36 | 6 |
| method | 3 | 3 | 2 | 2228610 | 14038 | 185 | 41 | 6 |
| method:candidate | 3 | 2 | 1 | 2376393 | 16673 | 202 | 44 | 5 |
| method:routed | 3 | 3 | 0 | 20848115 | 398236 | 4649 | 173 | 2 |

Roles and per-episode dollar cost:

| Episode | Arm | Role | Tier | Model | Tokens in | Tokens out | Episode $ |
|---|---|---|---|---|---|---|---|
| pilot-1 | control | n/a | n/a | claude-haiku-4-5-20251001 | 536622 | 4401 | 0.5586 |
| pilot-2 | control | n/a | n/a | claude-haiku-4-5-20251001 | 585752 | 4492 | 0.6082 |
| pilot-3 | method:routed | planner | frontier | claude-opus-5-5 | 4659025 | 129450 | 22.5770 |
| pilot-3 | method:routed | executor | fast | claude-haiku-4-5-20251001 | 1296079 | 11174 | 22.5770 |
| pilot-4 | method:routed | planner | frontier | claude-opus-5-5 | 3369305 | 88658 | 16.0766 |
| pilot-4 | method:routed | executor | fast | claude-haiku-4-5-20251001 | 791042 | 7038 | 16.0766 |
| pilot-5 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 708456 | 5942 | 0.7382 |
| pilot-6 | method | n/a | n/a | claude-haiku-4-5-20251001 | 711016 | 4663 | 0.7343 |
| pilot-7 | method | n/a | n/a | claude-haiku-4-5-20251001 | 766814 | 5589 | 0.7948 |
| pilot-8 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 856090 | 5116 | 0.8817 |
| pilot-9 | method:routed | planner | frontier | claude-opus-5-5 | 9259673 | 150245 | 41.5749 |
| pilot-9 | method:routed | executor | fast | claude-haiku-4-5-20251001 | 1472991 | 11671 | 41.5749 |
| pilot-10 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 811847 | 5615 | 0.8399 |
| pilot-11 | control | n/a | n/a | claude-haiku-4-5-20251001 | 768307 | 3507 | 0.7858 |
| pilot-12 | method | n/a | n/a | claude-haiku-4-5-20251001 | 750780 | 3786 | 0.7697 |

Audit:

- Clean: 11 of 12.
- pilot-5: 1 path(s) outside the episode directory (1 outside path(s), skill used: False).

## Smoke: smoke

- Cohort `2026-09-candidate-smoke`, seal `793c6229c4786b5dc2abbedc275bb85743bb1bb2a4f3cfafcab73432c0d186a9`, created 2026-09-26T12:14:12Z.
- Variants: `s62-caller-contract/v1` (development).
- Executor: claude-code-subagent, `claude-haiku-4-5`; as served: `claude-haiku-4-5-20251001`, `claude-opus-5-5`. Judge: mechanical hidden acceptance tests, blinded.
- Artifacts: candidate (9.0.0) `6acd83167c803ad260a2348bd9f6bc32b9d3d26a01ab18591903a00fed1ff2bd`; method (8.4.1) `n/a`.

```text
verdict[routing] s62-caller-contract/v1 unobserved method:candidate 1/1 [0.2065,1.0000] method:routed -/0 [n/a] p_better=n/a p_worse=n/a
```

| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | Files written | Check runs | Correction cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smoke-1 | s62-caller-contract/v1 | method:routed | invalid | invalid | 6497617 | 120466 | 1361 | 54 | 3 | 10 | 0 |
| smoke-2 | s62-caller-contract/v1 | method:candidate | fell | clean | 692345 | 3716 | 57 | 13 | 6 | 4 | 2 |

| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |
|---|---|---|---|---|---|---|---|---|
| method:candidate | 1 | 1 | 1 | 692345 | 3716 | 57 | 13 | 2 |
| method:routed | 1 | 0 | 0 | 6497617 | 120466 | 1361 | 54 | 0 |

Roles and per-episode dollar cost:

| Episode | Arm | Role | Tier | Model | Tokens in | Tokens out | Episode $ |
|---|---|---|---|---|---|---|---|
| smoke-1 | method:routed | planner | frontier | claude-opus-5-5 | 5003160 | 109984 | 23.7592 |
| smoke-1 | method:routed | executor | fast | claude-haiku-4-5-20251001 | 1494457 | 10482 | 23.7592 |
| smoke-2 | method:candidate | n/a | n/a | claude-haiku-4-5-20251001 | 692345 | 3716 | 0.7109 |

Audit:

- Clean: 1 of 2.
- smoke-1: 14 path(s) outside the episode directory (14 outside path(s), skill used: False).

## Decision

- `candidate`: **FAIL** (median tokens_in is not strictly lower for method:candidate)
- `routing`: **RECOMMENDATION** (median per-episode dollar cost is not equal or lower for method:routed)
