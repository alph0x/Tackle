# Decisions

Closed decisions — **don't revisit without cause**.

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-01 · Gate for Tackle 2.0 initiative · ✅ active · 2026-06-17, session 1

**Decision**: Full gate.
**Why**: The initiative changes the public surface (new triggers, new template directories), spans multiple sessions, and introduces a preset architecture.
**Supersedes**: none · **From**: intake default

## D-02 · Which spec-kit features to adopt · ✅ active · 2026-06-17, session 1

**Decision**: Adopt `constitution`, `specify`, `tasks`, `checklist`, and `presets`. Skip `analyze`, `clarify` (covered by intake), and `taskstoissues`.
**Why**: Adds the SDD chain without replicating spec-kit's optional/enterprise features. Keeps Tackle lean.
**Supersedes**: none · **From**: intake default

## D-03 · SDD framework shape · ⤴ superseded by D-03a

**Decision**: Optional SDD phases around an unchanged planning core. `/tackle-plan` remains the default; users can run the full chain or just plan.
**Why**: Preserves backward compatibility and Tackle's identity. A mandatory chain would push away users who only want action planning.
**Supersedes**: none · **From**: highest-shape decision

## D-03a · Execution mode for Tackle 2.0 · ✅ active · 2026-06-17, session 5

**Decision**: Tackle 2.0 adds execution. `/tackle-implement` runs the plan point-by-point inside the same conversation, updating `board.md` status and appending to `log.md` after each point.
**Why**: User wants Tackle to be more disruptive. Since Tackle already produces prompts, the next major-version jump is to consume them: the same skill that plans can also drive execution while keeping the workspace as the canonical state.
**Supersedes**: D-03 (optional phases only) · **From**: user override during planning

## D-04 · Skill vs CLI · ✅ active · 2026-06-17, session 1

**Decision**: Markdown skill first; `/tackle-init` is a trigger, not an external installer. No Python/Node CLI in 2.0.
**Why**: Maintains model-agnosticism and zero dependencies. A CLI can be reconsidered for 2.1 if adoption justifies it.
**Supersedes**: none · **From**: Q-02 provisional default

## D-05 · Extensions · ✅ active · 2026-06-17, session 1

**Decision**: No extension system in 2.0. Presets cover template customization.
**Why**: Extensions add a command-registration and lifecycle system that is not needed for a major-version value bump.
**Supersedes**: none · **From**: intake default

## D-06 · Plan-local layout · ✅ active · 2026-06-17, session 4

**Decision**: All Tackle customization artifacts live visibly inside `docs/plans/<initiative>/` (`constitution.md`, `presets/`, `overrides/`). No `.tackle/` hidden directory and no files at the repo root.
**Why**: Principles, presets, and overrides are first-class plan artifacts, not hidden config. This keeps every decision examinable and consistent with Tackle 1.5's visible workspace structure.
**Supersedes**: none · **From**: user feedback during planning

## D-07 · Variable execution team sizing · ✅ active · 2026-06-17, session 6

**Decision**: Point teams are sized by complexity: Solo / Pair / Pod / Squad. Default is Solo unless the briefing explicitly requests a larger team.
**Why**: Avoids the coordination overhead of a 4-agent pod for simple template creation while preserving the option for specialists on complex/high-risk points.
**Supersedes**: none · **From**: user feedback during execution
