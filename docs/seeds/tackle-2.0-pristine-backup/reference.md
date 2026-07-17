# Reference — current Tackle 2.0 codebase state

All claims below are verified against `~/Developer/Tackle`.

## File structure

```
~
├── README.md                 ← human-facing overview, triggers, pipeline summary
├── SKILL.md                  ← full methodology: routing, 11 steps, conventions
└── references/
    ├── CHANGELOG.md
    ├── README.tmpl.md
    ├── AGENTS.tmpl.md
    ├── plan.tmpl.md
    ├── point.tmpl.md
    ├── log.tmpl.md
    ├── todo.tmpl.md
    ├── questions.tmpl.md
    ├── decisions.tmpl.md
    ├── reference.tmpl.md
    ├── foundations.tmpl.md
    ├── design-contract.tmpl.md
    ├── execution-strategy.tmpl.md
    ├── external-question.tmpl.md
    ├── reference-docs-README.tmpl.md
    ├── lite-plan.tmpl.md
    ├── board.tmpl.md           ← NEW in 2.0
    ├── team.tmpl.md            ← NEW in 2.0
    ├── sdd/                    ← NEW in 2.0
    │   ├── constitution.tmpl.md
    │   ├── specify.tmpl.md
    │   ├── tasks.tmpl.md
    │   ├── implement.tmpl.md
    │   ├── next.tmpl.md
    │   └── checklist.tmpl.md
    └── presets/                ← NEW in 2.0
        ├── default/
        │   └── (mirror of core templates)
        └── sdd/
            └── (mirror of SDD phase templates)
```

## Trigger table (SKILL.md §Routing)

| Trigger | Mode |
|---|---|
| `/tackle-init [preset]` | Init |
| `/tackle-constitution` | Constitution |
| `/tackle-specify` | Specify |
| `tackle this` / `plan de acción` / `armar un plan` / `plan this out` / `iniciativa` | Plan |
| `/tackle-tasks` | Tasks |
| `/tackle-implement` | Implement |
| `/tackle-next` | Execute next |
| `/tackle-checklist` | Checklist |
| `resume` / `retomá <initiative>` | Resume |
| `how is <initiative> going?` / `status` / `seguimiento` | Status |
| `what plans are there?` / `qué iniciativas hay` | List |
| `give me the next point` / `qué sigue` | Next |
| `migrate` / `upgrade` / `modernizá <initiative>` | Migrate |
| `mejorá este plan` / `improve this plan` / `tackle-upgrade <initiative>` | Improve |

## SDD phase templates (new in 2.0)

- `references/sdd/constitution.tmpl.md`
- `references/sdd/specify.tmpl.md`
- `references/sdd/tasks.tmpl.md`
- `references/sdd/implement.tmpl.md`
- `references/sdd/next.tmpl.md`
- `references/sdd/checklist.tmpl.md`

## Presets (new in 2.0)

- `references/presets/default/` — mirrors core templates.
- `references/presets/sdd/` — mirrors SDD phase templates.

## Quality tooling

- No automated test runner in this repo.
- No linter/formatter configured.
- Verification is manual review of markdown + template placeholders.
- `references/CHANGELOG.md` tracks skill-version history.

## Gaps filled by 2.0

- ✅ `references/sdd/` phase templates.
- ✅ `references/presets/` customization layer.
- ✅ SDD phase triggers before/after planning.
- ✅ Visible plan-local customization tree (`presets/`, `overrides/`).
- ✅ Plan execution via `/tackle-implement` and `/tackle-next`.
- ✅ `team.md` and `board.md` depth artifacts.
