# Step 3 — Scaffold inside PLAN

PLAN creates `docs/plans/<initiative>/` at the decomposition stage. If this initiative has no
previously authorized gitignore decision, **ask the user explicitly**: "Should `docs/plans/` be
added to `.gitignore`?" If yes, append `docs/plans/` to `.gitignore`; if no, record the decision in
`decisions.md` as:

```markdown
## D-0x — gitignore for docs/plans/

- Decision: do not add `docs/plans/` to `.gitignore`.
- Reason: {{user's reason or "user wants plan history tracked"}}.
- Asked: {{date}}.
```

Never silently skip this question or invent a prior answer. Reuse an existing authorized decision
and apply the same gitignore treatment to `docs/seeds/` when repository convention 9 requires it.

This is the one scaffold decision for the initiative. It is part of PLAN preparation and does not
start a second planning session or require a manual Verify between scaffolding and readiness.

# Step 3.5 — Scaffold the core

Resolve the method root from the actual SKILL.md path once. Resolve linked paths from their
containing Markdown file; on a missing path inspect that directory instead of retrying guessed
prefixes. Reuse unchanged sections already read. Read core templates and triggered depth sections
once, fill concise task-specific content, and retain required fields without copying unrelated
mode instructions into the workspace. The core file map and readiness checks still apply.

Apply the selected gate before copying: None creates no workspace. Lite creates only `plan.md`,
`log.md`, and `usage.md`, with decisions/questions files when needed; it does not load or instantiate
Full templates. Its complete bodies and lifecycle rules are in `../lite-plan.tmpl.md`; do not copy the generic log or legacy usage template. The core copying procedure below applies to Full only. These gate-specific rules
also govern the file maps in the generic workspace templates.

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
