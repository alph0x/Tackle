# s24 — standalone-planning (self-containment) trap

**Trap:** a user asks for a feature — "agrega un comando que exporte el plan a JSON" — in a small repo that already holds a Tackle plan workspace, with everything under-specified: what "the plan" means, what the JSON must contain, and where it goes. The plausible-wrong action is jumping straight to an implementation (pick one interpretation silently, write code, no anchors, no plan). Under Tackle 5.0 the intake path also routed to companion skills (`superpowers` brainstorming, `karpathy-guidelines`, `clean-architecture`) and prompted to install missing ones. Tackle 5.1 is self-contained (D-11 — companion-skill requirement revoked): intake must extract the four anchors with zero missing-skill prompts and produce a plan artifact before any implementation.

**Arms:**
- **control** — no-skill free-styling: raw task, NO excerpt. The teeth test: expected to jump to code with no anchors and no plan.
- **method** — the 5.1.0 excerpt: `SKILL.md` routing (guide map, rules, executor contract, "Planning is self-contained") + `intake-and-gate.md` (the intake mode's destination guide — the feature under test) + `plan.tmpl.md` + `lite-plan.tmpl.md` (the plan-artifact shapes). Companion content is absent from the excerpt by construction — that absence IS the feature. `team.tmpl.md` / `design-and-contract.md` are not included: the seed (single feature request, small repo, Lite-sized gate) does not route to them, and the trap-design rule requires the destination guide for the mode the seed triggers (intake).

Both arms receive the identical fixture (`fixture/` — a small plan-tracker repo: `src/planner.py` `add`/`list` CLI over `notes.txt`, plus an existing `docs/plans/tracker/` plan workspace) and the identical task (`task.md`; the method instantiation embeds the excerpt, the control embeds none). The task never mentions companions, skills, install, intake, anchors, or the trap (anti-gaming).

**Pass:** the method arm (a) extracts or confirms the four intake anchors (problem, observable result, top 2 non-goals, highest-shape decision) BEFORE proposing any solution, (b) shows zero install/missing-skill prompts, (c) produces a plan artifact under `docs/plans/`. The control arm is the discrimination signal — a jump-to-code is the trap hit; if the control also does anchors + plan, record a null (valid outcome).

See `GROUND-TRUTH.md` for run records.
