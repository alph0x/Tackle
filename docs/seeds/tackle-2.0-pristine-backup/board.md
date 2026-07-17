# Board — Tackle 2.0

Canonical status board. Updated only by `/tackle-implement`, `/tackle-next`, or manually during a session.

| Point | What | Briefing | Depends on | Status |
|---|---|---|---|---|
| **P-00 · Walking skeleton** | Create the thinnest end-to-end SDD flow: stub templates for constitution/specify/plan/tasks/implement/checklist plus a temporary router so the chain can be demoed before any phase is real. | `points/P-00-walking-skeleton.md` | none | ⚪ skipped |
| **P-01 · Constitution phase** | Add `/tackle-constitution` trigger + `references/sdd/constitution.tmpl.md` template; produce `docs/plans/<initiative>/constitution.md`. | `points/P-01-constitution-phase.md` | none | 🟢 done |
| **P-02 · Specify phase** | Add `/tackle-specify` trigger + `references/sdd/specify.tmpl.md` for product specs / user stories. | `points/P-02-specify-phase.md` | none | 🟢 done |
| **P-03 · Tasks phase** | Add `/tackle-tasks` trigger + `references/sdd/tasks.tmpl.md`; decompose a plan into a task checklist. | `points/P-03-tasks-phase.md` | none | 🟢 done |
| **P-04 · Implement phase** | Add `/tackle-implement` and `/tackle-next` triggers + `references/sdd/implement.tmpl.md`; execute the plan point-by-point inside the workspace. | `points/P-04-implement-phase.md` | P-03 | 🟢 done |
| **P-05 · Checklist phase** | Add `/tackle-checklist` trigger + `references/sdd/checklist.tmpl.md`; generate a custom quality checklist from a spec or plan. | `points/P-05-checklist-phase.md` | none | 🟢 done |
| **P-06 · Template-resolution stack + presets** | Define how plan-local overrides, presets, and core templates resolve; add `references/presets/default/` and `references/presets/sdd/`. | `points/P-06-template-stack-and-presets.md` | P-01, P-02, P-03, P-04, P-05 | 🟢 done |
| **P-07 · Plan-local customization bootstrapper** | Add `/tackle-init` trigger that creates `docs/plans/<initiative>/presets/` and `docs/plans/<initiative>/overrides/` from `references/presets/`. | `points/P-07-local-init-bootstrapper.md` | P-06 | 🟢 done |
| **P-08 · Update SKILL.md routing and changelog** | Rewrite routing table, add phase triggers, document execution + presets/overrides, bump version to 2.0, update `README.md`. | `points/P-08-update-skill-and-changelog.md` | P-06, P-07 | 🟢 done |
| **P-09 · Thin SKILL.md** | Reduce SKILL.md verbosity: move detailed Steps to `references/GUIDE.md`, keep routing + core rules + links. | `points/P-09-thin-skill.md` | none | 🟢 done |

### Dependency graph

```
P-00 (walking skeleton) — optional early slice, no downstream dependents
P-09 (thin SKILL.md) — independent cleanup, no downstream dependents

P-01 (constitution) ──┐
P-02 (specify) ───────┤
P-03 (tasks) ──────────┼──► P-06 (template stack + presets) ──► P-07 (init bootstrapper) ──► P-08 (SKILL.md + changelog)
P-04 (implement) ──────┤       ▲
P-05 (checklist) ──────┘       │
                                └── P-04 depends on P-03
```

**P-00 note**: the walking skeleton is an optional first slice to validate the SDD chain shape. It does not gate P-01..P-05.
