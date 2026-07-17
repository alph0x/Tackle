# Step 3 — Location & gitignore

Create `docs/plans/<initiative>/`. **Ask the user explicitly**: "Should `docs/plans/` be added to `.gitignore`?" If yes, append `docs/plans/` to `.gitignore`; if no, record the decision in `decisions.md` as:

```markdown
## D-0x — gitignore for docs/plans/

- Decision: do not add `docs/plans/` to `.gitignore`.
- Reason: {{user's reason or "user wants plan history tracked"}}.
- Asked: {{date}}.
```

Never silently skip this question.

# Step 4 — Scaffold the core

Copy templates from `references/` and fill `{{PLACEHOLDERS}}`. Delete unused sections. Never leave empty slots you won't fill.

## Depth artifacts

Create only when their trigger fires:
- `foundations.md` — grounding table (decision → principle → source).
- `design-contract.md` — authoritative public surface points implement.
- `execution-strategy.md` — waves + quality gate + deferral.
- `team.md` — execution team roles and protocol.
- `board.md` — canonical status board for execution.
- `coordinator.md` — Coordinator continuity projection (multi-agent execution).
- `reports/` — point closure reports (created at first point close, Full gate).
- `reference-docs/` — read-only external snapshots.
