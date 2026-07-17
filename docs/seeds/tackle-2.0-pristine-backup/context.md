# Context — Tackle 2.0

## Objective

Make Tackle a lightweight, model-agnostic, specification-driven planning + execution workflow that agents can run end-to-end inside any repository: establish project principles (`constitution`), write product specs (`specify`), produce a technical plan (`plan`), decompose into tasks (`tasks`), execute the plan (`implement`), and validate quality (`checklist`).

## Expected result

- A single trigger word routes into any SDD phase (`tackle-init`, `tackle-constitution`, `tackle-specify`, `tackle-plan`, `tackle-tasks`, `tackle-implement`, `tackle-next`, `tackle-checklist`).
- Backward-compatible triggers (`tackle this`, `plan de acción`) still open the Create flow.
- `/tackle-implement` runs the plan point-by-point, updating `board.md` status and `log.md` after each point.
- New templates live under `references/sdd/` for phases and `references/presets/` for customization, resolved through a simple template stack.
- `/tackle-init` creates a visible, plan-local customization tree (`presets/` and `overrides/`) inside `docs/plans/<initiative>/`.
- The planning workspace (`docs/plans/<initiative>/`) remains the canonical handoff artifact; nothing Tackle-related lives at the repo root.

## Non-goals (out of scope)

- Tackle does **not** become a SaaS, orchestrator, or MCP server. It stays a skill that runs inside the user's repo.
- No external issue tracker integrations in 2.0 (GitHub Issues, Jira, Linear). Spec-kit has `taskstoissues`; we skip it.
- No GUI/IDE panel. Templates are markdown; agents consume them.

## Risks / dependencies

- **Risk:** scope creep toward becoming a full SDD CLI/orchestrator. **Mitigation:** hard non-goals above; execution stays inside the agent session, not a separate service.
- **Risk:** backward-incompatible trigger changes break existing users. **Mitigation:** keep old triggers intact; new ones are additive.
- **Risk:** preset system over-engineered. **Mitigation:** start with one default preset + one override directory; no extension marketplace in 2.0.
- **Risk:** execution loop edits files unsafely. **Mitigation:** only update `board.md` and `log.md`; never modify 🟢 points; respect dependency order.
