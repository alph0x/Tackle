# Baseline cohort 2026-09: Tackle 8.4.1 against no skill

Development-grade evidence (D-87). Each episode ran as a Claude Code subagent of the coordinating session, on the operator's machine and login, not in an isolated install: it started in the host repository (D-95), and every arm could reach the installed skill and that repository. The contamination audit (D-91, D-94, D-96, D-98) sees only what the transcript's tool calls name; an episode it flags is invalid and leaves the counts. The method arm is asked to read and follow the staged 8.4.1 skill (D-98), as a user who invokes it would; triggering is not measured. One seed per arm and variant (n_min 1) can reach only inert or inconclusive for a variant that is observed, so this report reads the pooled difference and the costs, not a per-variant claim.

Hypothesis: With the Tackle 8.4.1 method, a Haiku executor falls into the planning-outcome traps less often than with no skill.

Arms: `control` receives the task alone; `method` receives the task and the instruction to read and follow a staged copy of the 8.4.1 install (artifact `239ceb22fe0cc842393a7e0430b8dd8c0924139b2f64cd17261ffbb6ee041abe`).

## Pilot: held-out variants

- Cohort `2026-09-baseline`, seal `8bd52d76f103f5872f96d5dab46d3a69c68790e9bb4a626ed64c08996f44377b`, created 2026-09-25T16:35:36Z.
- Variants: `s62-caller-contract/h1` (held-out), `s63-documented-edge-rule/h1` (held-out), `s64-stored-data-compat/h1` (held-out).
- Executor: claude-code-subagent, `claude-haiku-4-5`; as served: `claude-haiku-4-5-20251001`. Judge: mechanical hidden acceptance tests, blinded.

```text
verdict s62-caller-contract/h1 inconclusive control 1/1 [0.2065,1.0000] method 1/1 [0.2065,1.0000] p_better=1.0000 p_worse=1.0000
verdict s63-documented-edge-rule/h1 inert control 0/1 [0.0000,0.7935] method 0/1 [0.0000,0.7935] p_better=1.0000 p_worse=1.0000
verdict s64-stored-data-compat/h1 inconclusive control 1/1 [0.2065,1.0000] method 1/1 [0.2065,1.0000] p_better=1.0000 p_worse=1.0000
pooled 0.0000 [0.0000,0.0000] seed=20260923 B=10000
```

| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | Files written | Check runs | Correction cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pilot-1 | s64-stored-data-compat/h1 | method | fell | clean | 972731 | 5871 | 89 | 18 | 4 | 4 | 2 |
| pilot-2 | s63-documented-edge-rule/h1 | method | avoided | clean | 761575 | 5666 | 75 | 14 | 5 | 4 | 2 |
| pilot-3 | s64-stored-data-compat/h1 | control | fell | clean | 638137 | 4986 | 64 | 12 | 4 | 2 | 0 |
| pilot-4 | s62-caller-contract/h1 | control | fell | clean | 390771 | 3023 | 42 | 7 | 1 | 0 | 0 |
| pilot-5 | s62-caller-contract/h1 | method | fell | clean | 800007 | 4736 | 69 | 15 | 6 | 4 | 2 |
| pilot-6 | s63-documented-edge-rule/h1 | control | avoided | clean | 440581 | 3642 | 48 | 8 | 3 | 0 | 0 |

| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |
|---|---|---|---|---|---|---|---|---|
| control | 3 | 3 | 2 | 1469489 | 11651 | 154 | 27 | 0 |
| method | 3 | 3 | 2 | 2534313 | 16273 | 233 | 47 | 6 |

Audit:

- Clean: 6 of 6.

## Smoke: the procedure check on a development variant

- Cohort `2026-09-baseline-smoke`, seal `63ed8de9867c824e201e69d3006f3f01dfb4202986bbc4a40f916ff654f8ffe5`, created 2026-09-25T16:35:16Z.
- Variants: `s62-caller-contract/v1` (development).
- Executor: claude-code-subagent, `claude-haiku-4-5`; as served: `claude-haiku-4-5-20251001`. Judge: mechanical hidden acceptance tests, blinded.

```text
verdict s62-caller-contract/v1 unobserved control -/0 [n/a] method -/0 [n/a] p_better=n/a p_worse=n/a
```

| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | Files written | Check runs | Correction cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smoke-1 | s62-caller-contract/v1 | control | invalid | invalid | 574368 | 3136 | 48 | 12 | 6 | 4 | 2 |
| smoke-2 | s62-caller-contract/v1 | method | invalid | invalid | 577248 | 3583 | 52 | 11 | 4 | 3 | 2 |

| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |
|---|---|---|---|---|---|---|---|---|
| control | 1 | 0 | 0 | 574368 | 3136 | 48 | 12 | 2 |
| method | 1 | 0 | 0 | 577248 | 3583 | 52 | 11 | 2 |

Audit:

- Clean: 0 of 2.
- smoke-1: 1 path(s) outside the episode directory (1 outside path(s), skill used: False).
- smoke-2: 1 path(s) outside the episode directory (1 outside path(s), skill used: False).

## Re-smoke: the corrected procedure (D-98)

- Cohort `2026-09-baseline-smoke-2`, seal `460c05a96a3966690071415eb7090966726ebc029f00e37c560145162dd99980`, created 2026-09-25T17:51:08Z.
- Variants: `s62-caller-contract/v1` (development).
- Executor: claude-code-subagent, `claude-haiku-4-5`; as served: `claude-haiku-4-5-20251001`. Judge: mechanical hidden acceptance tests, blinded.

```text
verdict s62-caller-contract/v1 inconclusive control 1/1 [0.2065,1.0000] method 1/1 [0.2065,1.0000] p_better=1.0000 p_worse=1.0000
```

| Episode | Variant | Arm | Outcome | Audit | Tokens in | Tokens out | Wall s | Tool calls | Files written | Check runs | Correction cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smoke2-1 | s62-caller-contract/v1 | control | fell | clean | 624027 | 3602 | 53 | 12 | 6 | 4 | 1 |
| smoke2-2 | s62-caller-contract/v1 | method | fell | clean | 652335 | 4378 | 64 | 12 | 6 | 4 | 2 |

| Arm | Episodes | Valid | Fell | Tokens in | Tokens out | Wall s | Tool calls | Correction cycles |
|---|---|---|---|---|---|---|---|---|
| control | 1 | 1 | 1 | 624027 | 3602 | 53 | 12 | 1 |
| method | 1 | 1 | 1 | 652335 | 4378 | 64 | 12 | 2 |

Audit:

- Clean: 2 of 2.
