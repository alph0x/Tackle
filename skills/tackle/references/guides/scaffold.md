# Scaffold — depth for the [PLAN card](plan-card.md)

<a id="step-3--scaffold-inside-plan"></a>
The card's step 3 links here for the whole scaffold procedure: the one gitignore decision, then
copying the core set. Nothing below is Depth-only; a Coordinated request reads it in full once,
at decomposition.

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

Public documentation and examples must not disclose private initiative state from `docs/plans/`
or `docs/seeds/`. Keep those artifacts outside the installed Markdown package; use synthetic examples.

This is the one scaffold decision for the initiative. It is part of PLAN preparation and does not
start a second planning session or require a manual Verify between scaffolding and readiness.

# Step 3.5 — Scaffold the core

Resolve the method root from the actual SKILL.md path once. Resolve linked paths from their
containing Markdown file; on a missing path inspect that directory instead of retrying guessed
prefixes. Reuse unchanged sections already read. Read core templates and triggered depth sections
once, fill concise task-specific content, and retain required fields without copying unrelated
mode instructions into the workspace. The core file map and readiness checks still apply.

Apply the selected gate before copying: None creates no workspace. Lite creates only `plan.md`,
`history.md`, and `resource-usage.md`, with decisions/questions files when needed; it does not load or instantiate
Full templates. Its complete bodies and lifecycle rules are in `../lite-plan.tmpl.md`. The core copying procedure below applies to Full only. These gate-specific rules
also govern the file maps in the generic workspace templates.
When the plan changes how the project is put together and `.tackle/map/architecture.json` does not exist,
offer once to create it, as the [architecture map guide](architecture-map.md) states, and write nothing without a yes.

Create the workspace by copying the core set from the §File map: nine artifacts from
`AGENTS.tmpl.md` plus an empty `tasks/`. Select `task-board.tmpl.md`, `history.tmpl.md` and
`resource-usage.tmpl.md` for their matching core files, with `.tmpl` stripped and
`{{PLACEHOLDERS}}` intact. Verify the resulting file list against the map before
continuing. Hand-copying is the canonical path; the repository's `references/`
template library is read-only during scaffolding, and initiative-specific edits
belong in the workspace copy. Before handoff, run this file-map check from the repository
root and correct any missing or old-name artifact; a claimed file count does not substitute for
this observed check:

```sh
ws=docs/plans/<initiative>
for name in README.md AGENTS.md plan.md task-board.md history.md resource-usage.md questions.md decisions.md reference.md; do
  [ -f "$ws/$name" ] || { echo "missing core: $name"; exit 1; }
done
[ -d "$ws/tasks" ] || { echo "missing core: tasks/"; exit 1; }
for name in board.md log.md usage.md points; do
  [ ! -e "$ws/$name" ] && [ ! -L "$ws/$name" ] || { echo "old-name artifact: $name"; exit 1; }
done
```

Compile each new Full brief from `task.tmpl.md` into `tasks/T-0N-<name>.md` and use
that exact T id in `plan.md` §5, `task-board.md`, dependencies and report references.
No other brief template exists: an older `P-` workspace is migrated before it runs
([forward only](migrate.md#forward-only)).
Write each brief's `**Effort**:` as one bare vocabulary token with no trailing punctuation;
row 12 validates the exact value.

After completing the brief and core files, run all 17 direct lint rows in `lint-spec.md`
before any PLAN handoff, including when a task remains Draft or a product question is unanswered.
Structural lint does not establish readiness: report that blocker separately. A missing
`resource-usage.md`, malformed status cell or invalid effort field is a failed scaffold.

Core copies include `resource-usage.md` from `resource-usage.tmpl.md` for new Full workspaces.
A ledger holds only the v2 lifecycle table of `resource-usage.tmpl.md`; an older ledger
reaches it through migration.
New workspaces declare `Schema: tackle-observability/2`; lifecycle rows start before substantive work, finish at close, or use `observe-incomplete` after interruption. Resource usage remains informative and never gates task closure.

## Depth artifacts

Create only when their trigger fires:
- `foundations.md` — grounding table (decision → principle → source).
- `design-contract.md` — authoritative public surface tasks implement.
- `team.md` — execution team roles and protocol (includes §Wave gates).
- `current-work.md` — Coordinator continuity projection (multi-agent execution).
- `reports/` — task closure reports (created at first task close, Full gate).
- `reference-docs/` — read-only external snapshots.

(`task-board.md` is a core artifact, not depth — it is copied by the scaffold, per the §File map in `AGENTS.tmpl.md`.)
