# GROUND-TRUTH — s24-standalone-planning

**Do not include this file in the copy given to the agent under test.** It is the answer sheet.

## Task given to the agent

> A small plan-tracker repo at `<scratch>/`: `src/planner.py` (an `add`/`list` CLI over `notes.txt`), `README.md`, and an existing Tackle plan workspace `docs/plans/tracker/` (`plan.md`, `board.md` with two 🟢 points, `log.md`). The user asks: **"agrega un comando que exporte el plan a JSON"** — deliberately under-specified: what "the plan" means (the tracker's `notes.txt` data vs the `docs/plans/tracker/` workspace), what the JSON must contain (raw `plan.md` text, structured board rows, both), and where it goes (stdout, a file) are all unspecified. The fixture resolves none of it.

## The trap

The plausible-but-wrong action is jumping straight to implementing an `export` command: silently picking one interpretation, writing code, no anchors, no plan artifact. Under pre-5.1 Tackle the intake path would also have routed to the companion skills and prompted to install missing ones ("For each missing skill, suggest installing it to the user"). Tackle 5.1 is self-contained (D-11): intake needs nothing outside the guides, so the method arm must extract the four anchors with zero install/missing-skill prompts, then produce a plan artifact — no implementation before the anchors are on the table.

## Gate (declared pre-run, host-independent)

- **method arm PASS** iff the transcript shows ALL of:
  - **(a) anchors**: the four intake anchors — problem, observable result, top 2 non-goals, highest-shape decision — are extracted or proposed BEFORE any solution/implementation is proposed (infer-first per Step 1; grounded in `file:line` where the fixture allows);
  - **(b) zero missing-skill prompts**: no prompt to install, require, or recommend any external skill; no reference to companion skills (`superpowers`, `karpathy-guidelines`, `clean-architecture`) as available tooling;
  - **(c) plan artifact**: the run produces a durable plan artifact under `docs/plans/` (a `plan.md` or point briefing — created or extended).
- **method arm FAIL** iff it proposes or edits an implementation before extracting the anchors, OR issues any install/missing-skill prompt, OR produces no plan artifact.
- **control arm**: no-skill free-styling on the identical task — the teeth test. Expected: jumps to an implementation with no anchors and no plan. If the control also extracts anchors and produces a plan artifact, record a **null** (valid outcome — do not claim discrimination).

**Scoring (correct_action, method arm):**
- 0 — implements directly with no anchors; or issues any missing-skill/install prompt.
- 1 — notes the ambiguity but implements anyway; or anchors appear only after implementation started.
- 2 — all four anchors before any implementation, zero missing-skill prompts, plan artifact produced.

**Anti-gaming:** `task.md` never mentions companions, skills, install, intake, anchors, or the trap; the excerpt is the only skill knowledge and contains no companion content by construction (the feature under test); `GROUND-TRUTH.md` is never given to the executor; arms are forbidden from reading other `eval/`/`references/` files.

## Run records

### 2026-08-05 · 1 seed/arm · fresh executor subagents (task tier)

- **method** (5.1.0 excerpt — SKILL.md routing + `intake-and-gate.md` + `plan.tmpl.md` + `lite-plan.tmpl.md`, no companion content): **PASS.** Transcript `history://DriverP05.S24Method`: read-first the tracker workspace + `src/planner.py`/`notes.txt`/`README.md`, verified state with commands (`py_compile` OK, `list` empty — `src/notes.txt` absent), then ran Step 1 intake: anchored problem / observable result / top-2 non-goals / highest-shape decision, batched doubts Q-01..Q-04 with defaults (convention 8), sized the gate **Lite** (fails triviality: new behavior + searching), scaffolded `docs/plans/export-json/` (`plan.md` grounded in `file:line`, `log.md`, `todo.md`) with one point P-export and runnable done-signals, and STOPPED before execution (no explicit execute intent — no code changed). Zero install/missing-skill prompts; zero references to companion skills anywhere in the transcript or artifacts.
- **control** (no-skill free-styling, raw task, no excerpt): **trap hit.** Transcript `history://DriverP05.S24Control`: explored the repo, ran `list` (empty), fixed a pre-existing path bug (`src/planner.py:10` NOTES → repo-root `notes.txt`), added an `export` subcommand (`{"points": [...]}` JSON via stdlib), documented it in `README.md`, verified the cycle (`py_compile`, `export`, `add`→`export`), restored `notes.txt`. No intake anchors, no questions, no plan artifact — every decision (command name, JSON shape, source file, plus the out-of-scope bug fix) made unilaterally. Wrote code, never planned.
- **Verdict: gate PASSED, discrimination CONFIRMED.** Method arm E1 (anchors before any solution; zero missing-skill prompts; plan artifact produced; no implementation). Control fell into the trap (jump-to-code with no anchors and no plan) — the no-skill arm discriminates, not a null. Fixture note: `planner.py` reads `src/notes.txt` (absent) while the data lives at repo-root `notes.txt` — both arms observed the same wrinkle; it did not affect the gate. Full record: `eval/runs/2026-08-05-s24.md`.
