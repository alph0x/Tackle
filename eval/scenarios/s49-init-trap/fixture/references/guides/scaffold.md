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

Create the workspace from the file map:

Copy the nine core templates into `docs/plans/<ws>/`, strip each `.tmpl` suffix, and create an empty `points/` directory.

The §File map's 9 artifacts from `AGENTS.tmpl.md` must be copied with `.tmpl` stripped and `{{PLACEHOLDERS}}` intact. Verify with an exhaustive listing of the expected paths and confirm no template suffix remains. The repository's `references/` template library is read-only during scaffolding; initiative-specific edits belong in the workspace copy.

Core copies include `usage.md` from `usage.tmpl.md` (every workspace born ≥ 5.2).

## Depth artifacts

Create only when their trigger fires:
- `foundations.md` — grounding table (decision → principle → source).
- `design-contract.md` — authoritative public surface points implement.
- `team.md` — execution team roles and protocol (includes §Wave gates).
- `coordinator.md` — Coordinator continuity projection (multi-agent execution).
- `reports/` — point closure reports (created at first point close, Full gate).
- `reference-docs/` — read-only external snapshots.

(`board.md` is a core artifact, not depth — it is copied by the scaffold, per the §File map in `AGENTS.tmpl.md`.)
