# AGENTS — Demo workspace

Methodology: Tackle 4.0.0
Autonomy level: L2 (assisted)

## File map

```
docs/plans/demo/
├── plan.md       ← objective, point decomposition
├── board.md      ← canonical status board for execution
├── log.md        ← append-only session log
├── usage.md      ← token/model/effort ledger
├── points/       ← one self-contained .md per point
└── AGENTS.md     ← this file
```

## Harness map

| Generic operation | Harness tool / command in this repo | Notes |
|---|---|---|
| Read code at `file:line` | `read`, `cat` | |
| Search code | `grep` | |
| Run tests / done-signal | `true` | point gate is a constant |
| Agent messaging | none | `agent-messaging: unsupported` |

## Model map

Tackle tiers are abstract; this map records which concrete model this harness offers for each tier. Update this section if the offerings change.

| Tier | Concrete model in this harness | Notes |
|---|---|---|
| `fast` | `acme-small` | |
| `standard` | `acme-base` | Driver binding |
| `frontier` | `acme-ultra` | Checker binding |

**effort-binding: unsupported**

## Executor contract (when you work a point)

Tackle planned this workspace; execution happens here, in sessions like yours. To keep
tracking alive, when you pick up, finish, pause, or abandon a point you MUST:

1. Set its status in `board.md` — fixed vocabulary: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done · ⚪ skipped (optional slice not executed, with one-line reason).
2. Append a `log.md` entry with an updated State snapshot. Never rewrite old entries.
3. If the code drifted from the point's `file:line` claims, update that point's Context.

Full conventions: `SKILL.md` §Core conventions.
