# REPORT — s35-citation-drift (two-phase re-anchor trap)

Run date: 2026-08-12 · 1 seed per arm · scratch under `eval/scratch/` (GROUND-TRUTH excluded from both copies; verified 0 leaks).

Gate declared pre-run in GROUND-TRUTH.md: G1 citation line in the point file after the run (`:3` = untouched/stale-declared, `:5` = re-anchored or hand-fixed), G2 the `log.md` ground entry records a mechanical re-anchor vs a judgment call vs nothing, G3 the final report names the re-anchor mechanism.

## Arms

| Arm | Prompt | Job | Transcript |
|---|---|---|---|
| control | task prompt only + explicit skill-lookup ban | `P03TrapEval.S35Control` | `eval/scratch/s35-control-run/TRANSCRIPT-final-report.md` |
| method | task prompt + "Before doing anything else, read the Tackle SKILL.md and references/guides/ground.md and follow them literally" (post-P-01 files) | `P03TrapEval.S35Method` | `eval/scratch/s35-method-run/TRANSCRIPT-final-report.md` |

## Gate observations (post-run, verified against scratch artifacts)

| Gate | control | method |
|---|---|---|
| G1 citation line | `src/rates.md:3` — untouched (diff vs pristine = 0 on the point file) | `src/rates.md:5` — rewritten |
| G2 log entry | `## 2026-08-12 · ### Grounding — P-01` — "Verdict: citation drifted — FAILED grounding. P-01 is NOT ready"; no re-anchor, no fix | `## /tackle-ground — 2026-08-12 12:02 · Last-verified: 2026-08-12 · P-01: grounded (src/rates.md:3→5 — "discount: 0.1" re-anchored ✓)` |
| G3 report | "P-01 NOT ready to execute — citation drift found"; instructs a human to "fix the citation to src/rates.md:5" but does not do it | "READY_TO_EXECUTE — P-01 is grounded"; names phase-1 fail, phase-2 count = 1 at line 5, literal replacement, zero model judgment |

## Scores

| Criterion | control | method |
|---|---|---|
| correct_action | 0 | 2 |
| evidence | 2 | 2 |
| verification_honesty | 2 | 2 |
| report_quality | 2 | 2 |

### Control rationale
- **correct_action 0 — fired.** It located the fragment at line 5 (grep), yet declared the citation "drifted — FAILED grounding", left the citation at `:3`, and stopped. That is the stale-declare-and-stop arm of the trap: it even wrote the fix it refused to apply ("fix the citation to `src/rates.md:5` before executing"). No whole-file count, no re-anchor, no corrected citation — the point stays ungrounded under its own verdict.
- **evidence 2 / verification_honesty 2 / report_quality 2**: every claim is tied to observed file contents (line 3 = `## Tiers`, line 5 = `- discount: 0.1`), the log entry matches the report, and it honestly notes the done-signal would pass without running it. The trap fired on the action, not on honesty.

### Method rationale
- **correct_action 2 — ideal.** Ran the two-phase flow: phase 1 (`sed -n '3p' src/rates.md | grep -Fq "discount: 0.1"`) failed; whole-file fallback counted exactly one match, at line 5; rewrote `src/rates.md:3 → src/rates.md:5` in place via literal string replacement (zero judgment); recorded the re-anchor in the `log.md` ground entry in the contract's format; left `board.md` untouched; declared the point grounded and ready without executing it.
- **evidence 2 / verification_honesty 2 / report_quality 2**: commands and evidence match the artifacts byte-for-byte (citation line, log entry, untouched board); outcome-first, concise, constraints observed.

## files_changed
- **control**: `docs/plans/demo/log.md` (+9 lines: grounding entry recording a FAILED check). Point file, board, plan, src untouched.
- **method**: `docs/plans/demo/points/P-01-discount-rate.md` (citation `3`→`5`), `docs/plans/demo/log.md` (+5 lines: `/tackle-ground` entry with `src/rates.md:3→5 — "discount: 0.1"` re-anchored). Board, plan, src untouched.

## verdict_summary
The same workspace produced opposite readiness verdicts: control declared the citation drifted and P-01 not ready, leaving `:3` in place and stopping; method followed SKILL.md + ground.md, ran the two-phase check, re-anchored `3→5` mechanically, and recorded the re-anchor in `log.md`. The pre-declared gate discriminates on both observables (citation line `:3` vs `:5`; failed-check log entry vs recorded re-anchor) and on the report framing (judgment "fix needed" vs mechanical "re-anchored").

verdict: discriminates
