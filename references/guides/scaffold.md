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

Create the workspace by copying the core set from the §File map: nine artifacts from
`AGENTS.tmpl.md` plus an empty `points/`, with `.tmpl` stripped and
`{{PLACEHOLDERS}}` intact. Verify the resulting file list against the map before
continuing. Hand-copying is the canonical path; the repository's `references/`
template library is read-only during scaffolding, and initiative-specific edits
belong in the workspace copy.

Core copies include `usage.md` from `usage.tmpl.md` (every workspace born ≥ 5.2).
New workspaces declare `Schema: tackle-observability/2`; lifecycle rows start before substantive work, finish at close, or use `observe-incomplete` after interruption. Usage remains informative and never gates point closure.

## Depth artifacts

Create only when their trigger fires:
- `foundations.md` — grounding table (decision → principle → source).
- `design-contract.md` — authoritative public surface points implement.
- `team.md` — execution team roles and protocol (includes §Wave gates).
- `coordinator.md` — Coordinator continuity projection (multi-agent execution).
- `reports/` — point closure reports (created at first point close, Full gate).
- `reference-docs/` — read-only external snapshots.

(`board.md` is a core artifact, not depth — it is copied by the scaffold, per the §File map in `AGENTS.tmpl.md`.)
