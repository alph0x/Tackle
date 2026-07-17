# AGENTS — Tally workspace

Methodology: Tackle 3.3.0
Autonomy level: L2 (assisted)

## Harness map

| Generic operation | Harness tool / command in this repo | Notes |
|---|---|---|
| Read code at `file:line` | `read`, `cat` | |
| Search code | `grep` | |
| Run tests / done-signal | `python tally.py` | |
| Spawn parallel agents | none — single-agent harness | |
| Agent messaging | none | `agent-messaging: unsupported` |

If this workspace is shared across agents, fill this map once and never assume a specific IDE, model, or vendor tool.

## Model map

Tackle tiers are abstract; this map records which concrete model this harness offers for each tier. Update this section if the offerings change.

| Tier | Concrete model in this harness | Notes |
|---|---|---|
| `fast` | `acme-small` | |
| `standard` | `acme-base` | Driver binding |
| `frontier` | `acme-ultra` | Checker binding |

**model-binding: supported** <!-- harness capability: can a spawn pin a concrete model for its tier? -->

Role bindings: Driver → `standard`; Checker → `frontier` (checker ≠ maker).

Full conventions: `SKILL.md` §Core conventions.
