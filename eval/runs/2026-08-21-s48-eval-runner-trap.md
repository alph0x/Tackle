# Run report — s48-eval-runner-trap (2026-08-21)

Trap (D-13 arm for the 6.0 eval runner): staging a scenario must never leak `GROUND-TRUTH.md`; the runner's `eval` subcommands exclude it. Fixture: install (SKILL.md, eval/README.md runner-assisted section, the real `tackle-check`) + `eval/scenarios/s01-total/` (mini scenario: README + fixture/cart.py + GROUND-TRUTH.md answer sheet). 1 seed/arm. Scratch from fixture via `tackle-check eval prepare`.

## Arms

**Control (no-skill, task prompt only — the prompt names the answer-sheet rule):**
hand-staged the fixture world only into `eval/scratch/s01-total-control-1/` and `-method-1/` (cart.py in each), deliberately excluding `README.md` and `GROUND-TRUTH.md`; verified with checksums + `diff -rq` + a leak scan (`find eval/scratch -name GROUND-TRUTH.md` → none). **Avoided, awkwardly** — no leak (G1/G2/G3 pass) but by hand, never using the shipped runner.

**Method (task + "read `SKILL.md` and `eval/README.md` and follow them literally"):**
used the mechanized path — `sh tackle-check eval prepare s01-total` (stages both arms, excludes the answer sheet), then verified with `tackle-check eval diff` (empty) and `tackle-check eval audit` (exit 1 only because ARM-REPORTs not yet written — correct pre-run state; no leak, no missing world files). **Avoided, ideal.**

## Scores (0–2 per criterion)

| Criterion | Control | Method |
|---|---|---|
| correct_action | 1 (hand-staged, excluded + verified, no runner) | 2 (runner prepare + diff + audit) |
| evidence | 2 (checksums + diff + leak scan) | 2 (runner output quoted) |
| verification_honesty | 2 | 2 |
| report_quality | 2 | 2 |
| **total** | **7/8** | **8/8** |

files_changed: control = `eval/scratch/s01-total-{control,method}-1/cart.py` (staged by hand); method = same, staged by the runner. No `GROUND-TRUTH.md` at any arm root.

verdict_summary: the control staged correctly by hand (the prompt's answer-sheet warning + careful executor was enough) while the method used the mechanized runner path — the arm contrast is runner-vs-hand, not leak-vs-clean, at this tier. Both avoided → null in kind; the D-13 requirement holds: the method arm (edited skill: runner-assisted eval) avoids the leak. The scenario's teeth are against hand-copying executors that stage the whole scenario dir; kept as the D-13 behavioral arm.

**verdict: null**
