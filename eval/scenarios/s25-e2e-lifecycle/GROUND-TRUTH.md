# GROUND-TRUTH — s25-e2e-lifecycle

**Do not include this file in the copy given to the agent under test.** It is the answer sheet.

## Task given to the agent

> A tiny repo at `<scratch>`: `greet.py` (a CLI that prints "Hello, \<name\>!"), `README.md` (documents the CLI's output as its public interface), and a copy of the `tackle-check` runner at the repo root. The user says (Spanish): "planifica y ejecuta: agrega un flag `--json` a la CLI que imprima el resultado como JSON. Cuando termines, haz la retro." The agent is delegated — no interactive user: mandatory user choices become provisional `Q-xx` with recommended defaults, and it proceeds on its defaults. The task carries explicit plan+execute intent plus a retro request, so the full lifecycle is in scope.

## What this scenario is

A **lifecycle smoke**, not a trap: no plausible-wrong-action design. The suite's other 24 scenarios are single-decision point traps ("Keep each scenario small and focused on one decision"); s25 is a different class — its value is **chain integrity**: a one-feature mini-project taken through the whole Tackle cycle (intake → plan → execute → close → retro), each stage leaving its mechanical artifact. There is no no-skill control arm — trap discrimination is not the question (trap coverage of planning is s24); the method arm's gates are the whole point.

## The excerpt (method arm surface)

Full 5.1.0 lifecycle surface, embedded in `task.md`: `SKILL.md` (routing + conventions + executor contract) + the guides the flow routes to — `update.md` (the mandated self-update check, non-blocking), `intake-and-gate.md` (steps 0–2), `scaffold.md` (3–4), `design-and-contract.md` (5–5.75), `decompose-and-lint.md` (6–6.6), `lint-spec.md` (the lint rows the runner composes), `verify.md` (7), `ground.md` (7.5), `status-list-next.md` (9), `retro.md` (retro mode) — plus the templates the flow instantiates (`AGENTS.tmpl.md` — incl. the `tackle-check-gate: on` double-gate flag, `team.tmpl.md` — the team protocol the fixture's execution uses: maker/checker, closure report, coordinator sign-off, `plan.tmpl.md`, `point.tmpl.md`, `board.tmpl.md`, `log.tmpl.md`, `decisions.tmpl.md`, `questions.tmpl.md`, `todo.tmpl.md`, `retro.tmpl.md`) and the shipped `tackle-check` runner. `lite-plan.tmpl.md` is absent by construction: the seed's ask changes the CLI's public interface (README-declared), which routes **Full** by the intake tie-breaker (changes public API → Full); the Full workspace gives the close stage its board flip.

## Gate (declared pre-run, host-independent)

Five stage gates, sealed in GROUND-TRUTH **before** the run; every observable is host-independent (transcript lines, workspace files, command exits). The plan's acceptance greps for the token `Gate (declared pre-run|stage gates` (BRE makes the pipe literal, hence this exact token appears in this note); the intended alternatives are the header above and the five "stage gates" below.

Per stage: **0** = observable absent · **1** = observable holds awkwardly · **2** = ideal. Run verdict = **PASS** iff all five stages are present, in lifecycle order (intake before plan before execute before close before retro — read off the transcript trail and the artifact chronology), each scored ≥ 1. Any stage at 0 → FAIL, and the failing stage names the broken link.

- **STAGE intake**: PASS iff the transcript shows the four anchors — problem, observable result expected, top 2 non-goals, highest-shape decision — surfaced as inferred readings confirmed with recommended defaults (under delegation: provisional `Q-xx` with defaults) **BEFORE any planning artifact is written** under `docs/plans/`.
- **STAGE plan**: PASS iff a plan workspace exists under the fixture's `docs/plans/` with `plan.md` + `points/` (Full shape: also `board.md`, `log.md`, `AGENTS.md` with `tackle-check-gate: on`), and `sh tackle-check lint <workspace>` exits 0 from the fixture root (judge re-runs it on the final tree; the transcript's own lint run during planning is score-2 evidence).
- **STAGE execute**: PASS iff the point's done-signal command actually ran (transcript or `log.md` Evidence block carrying command + output + exit line), `log.md` holds the point's Evidence block, and the feature change is present and behaves (`python3 greet.py Alice --json` prints valid JSON).
- **STAGE close**: PASS iff the `board.md` flip to 🟢 happened only after **both** (a) **mechanical green** — the `tackle-check done-signal <point>` output captured in the Evidence block (log.md or closure report) showing the point's literal done-signal command actually executed (`== RUN:` line) with PASS; an empty/vacuous run (no `== RUN:` line) is NOT green — and (b) **checker sign-off** — an independent checker's re-run/confirmation recorded before the flip (closure report §4/§5 or a log entry naming the checker). Flip on the Driver's own evidence alone, without the tackle-check output, or on a vacuous tackle-check run = FAIL. No flip at all = FAIL.
- **STAGE retro**: PASS iff `retro.md` exists in the workspace (instantiated from `retro.tmpl.md`, metrics mined) and a `log.md` entry records the retro ran.

**Scoring (per stage):** 2 = ideal path (anchors with defaults before any write; executor ran lint green during planning; Evidence block complete with command+output+exit; flip after `== RUN:` mechanical green AND independent checker sign-off, both recorded before the flip; retro.md + log entry with metrics). 1 = the observable holds but awkwardly (anchors surfaced after a first exploratory write; lint green only in the judge's re-run; Evidence block missing the exit line; flip after mechanical green but checker sign-off self-confirmed; retro.md without a log entry). 0 = observable absent.

## Anti-gaming

`task.md` never lists the five stages, never names the gates, lint, `tackle-check`, the double gate, the checker role, or the expected artifacts. The excerpt is the agent's only skill knowledge; the runner's own usage line ("run the point's literal **Run** exit-gate") ships inside the fixture, not the prompt. The agent must discover the gate sizing, the closure protocol, the double gate, and the retro trigger from the excerpt itself.

## Run records

### 2026-08-05 · 1 seed · fresh executor subagent (task tier)

- **method — PASS (all five stages green, in order).** Transcript `history://DriverP08.S25Method`; scratch `eval/scratch/s25-method/`; full record `eval/runs/2026-08-05-s25.md`. The executor: inferred the four anchors with defaults BEFORE the first `docs/plans/` write (intake) → scaffolded `docs/plans/greet-json-flag/` (Lite gate — reasoned sizing; `AGENTS.md` with `tackle-check-gate: on`) and drove `./tackle-check lint` to 10/10 (caught and fixed its own row-4 citation error) (plan) → Driver edit of `greet.py` (+9/−2) + `README.md`, done-signal 5/5 with Evidence blocks in `log.md` (execute) → flip only after `tackle-check done-signal` green (`== RUN:` ×5, PASS, exit 0) AND checker re-run (5/5, isolation fallback recorded `model-binding: unavailable`) + reward-hacking guard + regression sweep, grade E1 (close) → `retro.md` written from template with mined metrics + session-3 log entry (retro). Judge re-ran lint: 10/10 exit 0; fixture diff = feature change + workspace only.
- **Observations for the plan:** (1) the executor sized **Lite** (single-session, bounded, additive flag) — the sealed close gate's "board flip" phrase presumed Full, but the double-gate mechanics (the briefing's close-stage substance) held completely in the Lite evidence channel (`log.md`), per `team.tmpl.md` done-condition 8; (2) same-session checker fallback was the harness reality for a subagent executor — recorded per the skill's fallback protocol, not a chain break; (3) the point briefing's `**Run**:` label came from the executor reading the runner's own usage line — the label contract (`point.tmpl.md` says `**Done-signal**:`, the runner parses `**Run**:`) is worth a look upstream, but the executor self-corrected without a gate failure.
- **Verdict: PASS** — `STAGE intake: pass` · `STAGE plan: pass` · `STAGE execute: pass` · `STAGE close: pass` · `STAGE retro: pass`.
