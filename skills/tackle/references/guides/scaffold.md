# Scaffold — depth for the [PLAN card](plan-card.md)

<a id="step-3--scaffold-inside-plan"></a>
The card's step 3 links here for the whole scaffold procedure: the one gitignore decision, then copying the
core set. Nothing below is Depth-only; a Coordinated request reads it in full once, at decomposition.

PLAN creates `docs/plans/<initiative>/` at decomposition. With no previously authorized gitignore decision
for this initiative, **ask the user explicitly**: "Should `docs/plans/` be added to `.gitignore`?" If yes,
append `docs/plans/` to `.gitignore`; if no, record the decision in `decisions.md` as:

```markdown
## D-0x — gitignore for docs/plans/

- Decision: do not add `docs/plans/` to `.gitignore`.
- Reason: {{user's reason or "user wants plan history tracked"}}.
- Asked: {{date}}.
```

Never silently skip this question or invent a prior answer. Reuse an existing authorized decision, and apply
the same gitignore treatment to `docs/seeds/` when repository convention 9 requires it.

Public documentation and examples must not disclose private initiative state from `docs/plans/` or
`docs/seeds/`: keep those artifacts outside the installed Markdown package and use synthetic examples.

This is the initiative's one scaffold decision, part of PLAN preparation: it starts no second planning
session and requires no manual Verify between scaffolding and readiness.

# Step 3.5 — Scaffold the core

Resolve the method root once from the actual SKILL.md path, and linked paths from their containing Markdown
file; on a missing path inspect that directory instead of retrying guessed prefixes. Reuse unchanged sections
already read. Read core templates and triggered depth sections once, fill concise task-specific content, and
keep required fields without copying unrelated mode instructions into the workspace. The core file map and
readiness checks still apply.

Apply the selected gate before copying: None creates no workspace. Lite creates only `plan.md`, `history.md`
and `resource-usage.md`, with decisions/questions files when needed, and loads or instantiates no Full
templates; its complete bodies and lifecycle rules are in `../lite-plan.tmpl.md`. The core copying procedure
below is Full only. These gate-specific rules also govern the file maps in the generic workspace templates.
When the plan changes how the project is put together and `.tackle/map/architecture.json` does not exist,
offer once to create it, as the [architecture map guide](architecture-map.md) states, and write nothing without a yes.
When that base exists and the plan adds or changes components, PLAN writes `<workspace>/map-delta.json`, as
the [delta](architecture-map.md#the-delta) states.
When the plan adds, changes or retires required behavior, PLAN writes `<workspace>/requirements-delta.md`, as the [requirements base](requirements-base.md) states.

Create the workspace by copying the core set from the §File map: nine artifacts from `AGENTS.tmpl.md` plus
an empty `tasks/`. Select `task-board.tmpl.md`, `history.tmpl.md` and `resource-usage.tmpl.md` for their
matching core files, `.tmpl` stripped and `{{PLACEHOLDERS}}` intact, and verify the file list against the
map before continuing. Hand-copying is the canonical path; the repository's `references/`
template library is read-only during scaffolding, and initiative-specific edits
belong in the workspace copy. Before handoff, run this file-map check from the repository root and correct
any missing or old-name artifact; a claimed file count never substitutes for it:

```sh
ws=docs/plans/<initiative>
for name in README.md AGENTS.md plan.md task-board.md history.md resource-usage.md questions.md decisions.md reference.md; do
  test -f "$ws/$name" || { echo "missing core: $name";exit 1;}
done
test -d "$ws/tasks" || { echo "missing core: tasks/";exit 1;}
for name in board.md log.md usage.md points; do
  test ! -e "$ws/$name" -a ! -L "$ws/$name" || { echo "old-name artifact: $name";exit 1;}
done
```

Compile each new Full brief from `task.tmpl.md` into `tasks/T-0N-<name>.md` and use that exact T id in
`plan.md` §5, `task-board.md`, dependencies and report references. No other brief template exists: an older
`P-` workspace is migrated before it runs ([forward only](migrate.md#forward-only)). Write each brief's
`**Effort**:` as one bare vocabulary token with no trailing punctuation; row 12 validates the exact value.

After completing the brief and core files, run all 19 direct lint rows in `lint-spec.md` with
[`scripts/lint.py`](../../scripts/lint.py), which the plan request authorizes
([script consent](../../scripts/README.md#consent)), before any PLAN handoff, even when a task stays Draft
or a product question is unanswered. Structural lint does not establish readiness: report that blocker
separately. A missing `resource-usage.md`, malformed status cell or invalid effort field is a failed scaffold.

Core copies include `resource-usage.md` from `resource-usage.tmpl.md` for new Full workspaces. A ledger holds
only the v2 lifecycle table of `resource-usage.tmpl.md`; an older ledger reaches it through migration. New
workspaces declare `Schema: tackle-observability/2`; lifecycle rows start before substantive work, finish at
close, or use `observe-incomplete` after interruption. Resource usage stays informative and never gates task
closure.

## Depth artifacts

Create only when their trigger fires:
- `foundations.md` — grounding table (decision → principle → source).
- `design-contract.md` — authoritative public surface tasks implement.
- `team.md` — execution team roles and protocol (includes §Wave gates).
- `current-work.md` — Coordinator continuity projection (multi-agent execution).
- `reports/` — task closure reports (created at first task close, Full gate).
- `reference-docs/` — read-only external snapshots.
- `findings.md` — finding ledger of a multi-round verification ([verification rounds](verify.md#verification-rounds)).

(`task-board.md` is a core artifact, not depth: the scaffold copies it, per the §File map in `AGENTS.tmpl.md`.)

## Sibling workspaces

A workspace may declare sibling workspaces in its AGENTS.md, and a task may then depend on a sibling's task as T-NN [sibling] or keep its brief under that sibling's tasks/.

A row of a `## Sibling workspaces` table in AGENTS.md, under the header `| Sibling | Path | Relation |`, declares a sibling; its path must be `docs/plans/` followed by one folder name. Rows, comments and fenced blocks are read as the plan view reads them, and a row failing these checks declares nothing. A dependency on a sibling's task is written `T-NN [sibling]` with exactly one space; repeated references in one cell count once. A brief may be `../<name>/tasks/<file>` when `<name>` is a declared sibling, resolving only under that sibling's tasks/ folder. Lint row 2 checks each sibling a dependency names, reporting an undeclared sibling, a missing or older sibling task-board.md, and a task id not on that board; a sibling named only by a brief is not checked. A task whose sibling dependency is not Complete is not Ready to run; lint does not check that state.

<a id="multi-repository-workspace"></a>
## Multi-repository workspace

One workspace, in the repository where planning happens, may plan work that lands in several repositories.
Its `AGENTS.md` then holds the Repositories table, and each brief states `**Repository**: <id>`.
A task's Write scope paths are relative to its repository's root, and a task writes only inside its own repository.
Each repository keeps its own requirements base and its own gitignore answer (see the requirements base guide), and each delta entry names its `Repository:`.
Lint row 8 compares Write scope paths as text across active workspaces, so two workspaces naming the same relative path in different repositories are reported as a collision; read the Repository fields to resolve it. Row 8 does not compare tasks within one workspace.
A single-repository workspace has no Repositories table and no Repository field.
