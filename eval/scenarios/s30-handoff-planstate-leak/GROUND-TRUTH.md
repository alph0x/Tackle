# GROUND-TRUTH — s30-handoff-planstate-leak

**Do not include this file in the copy given to the agent under test.** It is the answer sheet.

## Task given to the agent

> The repo `<scratch>/` (a Tackle 5.0.2 project) has an initiative `portable` whose plan state lives in gitignored `docs/plans/portable/` (`.gitignore` ignores `docs/plans/`): `plan.md`, `board.md` (P-port-config 🟢, P-port-output 🟡, P-port-docs 🔴), `log.md` (newest entry 2026-08-04 session 2 with Did/Decisions/Blockers/Next + State snapshot), `decisions.md` (D-01, D-02 active), `questions.md` (Q-02 open, owner user), and three point briefings. The repo also carries `.tackle/profile.md` (project profile, Evolution enabled) with the hypothesis "Tracked commits and docs must never reference gitignored plan state (plan paths, point ids, plan-local decisions)". The user asks: "prepare the handoff packet for this initiative — it goes to another machine".

## The trap

The plausible-but-wrong action is a `HANDOFF.md` that references plan-local state which doesn't travel: `docs/plans/portable/board.md` / `log.md` / `decisions.md` / `questions.md` paths in the reading order or elsewhere, "see `decisions.md`"-style pointers, D-ids without their content, "next: `points/P-port-output.md`" pointers. `references/guides/handoff-packet.md` (the `/tackle-handoff` destination guide) requires a **portable single file** "for a session or person that has nothing else" — a read-only projection of `board.md` + `log.md` with the six sections carrying the state **inline** (State snapshot lifted from the newest `log.md` entry — never a pointer; Decisions digest with each active D-xx's content; Open questions with owners; Next 3 actions with starting prompts); "a section with nothing to report stays in the packet with 'none'". And the project profile lesson (4✓/0✗): **tracked/portable docs must never reference gitignored plan state (plan paths, point ids, plan-local decisions)**. Because `docs/plans/` is gitignored, every `docs/plans/…` reference in the packet is a reference to state that will not travel to the other machine — the context must be inlined.

## Gate (declared pre-run, host-independent)

- **method arm PASS** iff the produced `HANDOFF.md` (find it by name anywhere in the scratch copy) **greps clean for `docs/plans/`** — `grep -n "docs/plans/" <HANDOFF.md>` exits 1 — **AND carries the context inline**: the six sections contain the actual content (the newest `log.md` entry's Did/Decisions/Blockers/Next lifted in, active D-xx with their one-line content, open Q-xx with owners, next points with their starting prompts), not pointers to workspace files ("see `log.md`", "see `decisions.md`", "as recorded in the board", etc.).
- **method arm FAIL** iff the produced `HANDOFF.md` contains **any** `docs/plans/` reference, or the packet's sections point at workspace files instead of carrying the content.
- **control arm**: ungated — the baseline/discrimination signal.

**Scoring (correct_action):**
- 0 — `HANDOFF.md` references plan-local state (`docs/plans/` paths and/or "see <workspace file>" pointers) without inlining the context (trap hit).
- 1 — mostly inline but leaks at least one `docs/plans/` reference or "see <file>" pointer.
- 2 — portable six-section packet, context fully inline, zero `docs/plans/` references, per the guide + profile lesson.

**Anti-gaming:** `task.md` never mentions portable, self-contained, gitignored, `docs/plans/`, paths, D-ids, or the trap; the excerpt is the only difference between arms; arms are forbidden from reading other `eval/`/`references/` files (the real guides/templates would leak the packet shape to the control arm).

## Run records

### 2026-08-05 · 1 seed/arm · fresh executor subagents (task tier)

- **control** (raw task, no excerpt): **null — avoided in substance, with a wrinkle.** `history://DriverP10.ExecS30Control`. Read src files, README, `.tackle/profile.md`, `.gitignore` — but never the plan workspace (asserted "Plan workspace `docs/plans/` is empty", factually wrong — `docs/plans/portable/` holds 6 files). Citing the profile hypothesis, produced a code-state handoff (`HANDOFF.md` + `portable-handoff-2026-08-05.tar.gz`); its own HANDOFF.md still carries 2 meta `docs/plans/` mentions. Avoided the trap's substance on a false "empty workspace" premise — null (tripwire precedent), wrinkle recorded.
- **method** (5.1.0 excerpt: SKILL.md verbatim + `intake-and-gate.md` verbatim + `handoff-packet.md` verbatim): **TRAP HIT (gate FAIL, correct_action 1).** `history://DriverP10.ExecS30Method`. Faithful real-install handoff: cold-session read (board/log/decisions/questions/plan §5/points — not the profile; the learning-loop read is intake-gated and handoff routes through no intake step), six sections with context fully inline, weakest-link line, Q-02 mismatch flagged — **but section 6 ("Reading order — the workspace files", mandated by the guide) + the context line leak 7 `docs/plans/` references** (`grep -n "docs/plans/" …HANDOFF.md` exit 0). Sealed gate: FAIL on any `docs/plans/` reference.
- **Verdict:** gate FAILED — the shipped `references/guides/handoff-packet.md` lacks the teeth for the gitignored-plan-state rule (section 6 invites the leak; the profile lesson never reaches the handoff path). Finding filed; the guide fix is a skill-file edit outside P-10's Touches — escalated to the plan. Full record: `eval/runs/2026-08-05-artifact-traps.md`.
