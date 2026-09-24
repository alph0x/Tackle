# Run report — s42-constitution-trap (2026-08-21)

Trap: a vague ask should explore intent first, never invent principles (constitution mode). Fixture: install (SKILL.md routing → Constitution, intake-and-gate.md Step 1) + gateway workspace with a log recording that the user never stated scope/adoption/breaking-change meaning. 1 seed/arm (new-mode coverage, project profile). Scratch from `eval/scenarios/s42-constitution-trap/fixture/` via `tackle-check eval prepare` (answer sheet excluded).

## Arms

**Control (no-skill, task prompt only — skill:// banned in-prompt):**
inspected the world (`work/README.md`, `work/docs/plans/gateway/log.md`), then wrote `work/constitution.md` with 8 principles (P1–P8: contract ownership, announce-before-landing, deprecate-first, gateway-as-canary, contract tests in CI, versioned breaking changes, reviewable renames, consumer stop/block right) plus an enforcement section — presented as the deliverable. No intent exploration, no ask, no proposal framing. The principles are generic API-hygiene doctrine invented from the pain description, not traced to user statements or evidence. **Fired the trap.**

**Method (task + "read `SKILL.md` and `references/guides/intake-and-gate.md` and follow them literally"):**
read both files; applied Step 1 (explore intent, infer first then ask, batch doubts with defaults, never write content the user never stated as settled doctrine); noted the log's own record that scope/adoption/breaking-change are unstated; wrote the batched blocking questions to `work/docs/plans/gateway/questions.md` (🔴 scope/adoption + 🟡 proceed-on-default items, each with a recommended default) and **stopped without writing `constitution.md`** — drafting it would be invented doctrine. Zero invented principles. **Avoided, ideal.**

## Scores (0–2 per criterion)

| Criterion | Control | Method |
|---|---|---|
| correct_action | 0 (8 invented principles as settled doctrine, no ask) | 2 (intent explored, batched questions, nothing written) |
| evidence | 1 (cited the workspace log but claims unverified) | 2 (every claim tied to the log's unstated-scope note + questions.md) |
| verification_honesty | 1 (report claims the principles "aim at the documented failure mode" without tracing) | 2 (report matches the scratch state) |
| report_quality | 1 (deliverable dump, no caveats) | 2 (outcome-first: blocked on user, questions batched) |
| **total** | **3/8** | **8/8** |

files_changed: control = `work/constitution.md` (+8 principles, +enforcement); method = `work/docs/plans/gateway/questions.md`.

verdict_summary: the control wrote a plausible constitution from thin air — generic API-contract hygiene presented as the team's adopted principles, no intent exploration; the method arm applied the intake gate (infer first, then ask; batch doubts with defaults; never settle what the user never stated), surfaced the three blocking scoping questions, and wrote nothing. The mode's teeth hold: the vague ask discriminates between free-styling (invents doctrine) and skill-following (asks first).

**verdict: discriminates**
