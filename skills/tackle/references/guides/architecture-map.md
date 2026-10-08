# Architecture map

The architecture map shows how a project is put together. The [plan view](plan-view.md) draws it twice: as
the project is today, and as it will be after the plan. The map has a base, which the project keeps, and a
delta, which each plan keeps in its workspace.

## The base

The base is `.tackle/map/architecture.json`, beside the project's Tackle profile. It is local and gitignored,
as the profile is. The map is not a profile hypothesis: only the owner's request or a confirmed closure fold
writes it, and `/tackle-retro` never does. Tackle deletes nothing from it.

Schema `tackle-map/1`:

```json
{
  "schema": "tackle-map/1",
  "project": "Name",
  "summary": "One sentence on what the project is.",
  "verified_at": {"revision": "v1.0.0", "commit": "abc1234", "date": "2026-10-01"},
  "groups": [{"id": "core", "title": "Core"}],
  "components": [{"id": "store", "group": "core", "title": "Store", "text": "What it does.",
                  "sources": ["src/store.py"]}],
  "relations": [["intake", "store", "calls"]]
}
```

A component's `sources` are repository-relative paths or glob patterns. A relation is `[from, to, label]`, and both ends are
component ids.

## No base

When no base exists, the view says so, and Tackle offers once to create one. Tackle never invents a map. It
reads the repository, proposes groups, components and relations with a source path it has seen for each, and
shows them. It writes the file only after the owner says yes, and it tells the owner that `.tackle/` should
stay out of version control.

## The delta

Each plan records its delta in `<workspace>/map-delta.json`, schema `tackle-map-delta/1`:

```json
{
  "schema": "tackle-map-delta/1",
  "plan": "Plan name",
  "base_revision": "v1.0.0",
  "changes": [
    {"op": "change", "id": "store", "text": "New text.", "task": "T-<id>", "state": "done"},
    {"op": "add", "id": "viewer", "group": "core", "title": "Viewer", "text": "What it does.",
     "task": "T-<id>", "state": "planned", "relations": [["intake", "viewer", "calls"]]}
  ]
}
```

- `op` is `add` or `change`. A change names the component `id` and the fields it adds or changes.
- `task` names the task that owns the change. `state` is `planned` until that task is Complete, then `done`.
- `relations` is optional and adds relations.

When a base exists and the plan adds or changes components, PLAN writes this delta with the plan, each
change `planned`. Validating it with the recipe needs the owner's explicit authorization, which an
architecture-map or plan-view request grants; without that grant, the next view build checks the delta and
refuses an invalid one.

## The recipe

Saving and importing the recipe needs the owner's explicit authorization; an explicit architecture-map or plan-view request, or the owner's closure-fold confirmation, grants it for that request ([recipe consent](../recipes/README.md#consent)). Prefer an equivalent harness capability. With that authorization, save the [recipe](../recipes/architecture-map.md) as a file and import it. It uses only the standard library
and changes none of its inputs:

- `validate(base, delta)` lists every problem. It names a change of an unknown component, an add of an
  existing one, an unknown group, a relation end that is missing after the changes, and an `op` or `state`
  outside the vocabulary.
- `after(base, delta)` returns the base with every change applied, and raises `ValueError` on a problem.
- `neighbors(map, ids)` returns the ids and every component related to one of them, in either direction.
- `stale(map, root)` returns the ids of components whose source path is missing under `root`.
- `fold(base, delta, revision)` returns a new base with only the `done` changes, and raises `ValueError` on a
  problem. `planned(delta)` lists the changes it leaves out.

## The view

Build the plan view with the base:

```sh
python3 -I plan-view.py --template plan-view.template.md --map .tackle/map/architecture.json \
  --map-scope all <workspace> <workspace>/plan-view.html
```

The page gains a Before and after section with a Cards tab and a Diagram tab, for Today and for After this
plan. New and changed components carry their task and state. With no delta, the section shows only today.
Without `--map`, or when the `--map` file does not exist, the island's `map` is null, and a workspace that has
a delta or a `--map` gets a note that there is no base map yet. An unreadable base or a wrong field type refuses,
and the refusal names the field.

The recipe reads `<workspace>/map-delta.json` and resolves source paths against the repository root, three
levels above the workspace. A component whose source path no longer exists, or whose glob pattern matches nothing, shows as stale. The view
refuses an invalid delta, names the problem and writes no file.

## Large project

A project of more than 25 components is large. Before the first build for it, ask the owner what to show:
the whole map (`--map-scope all`), or only the changed components with their neighbors
(`--map-scope changed`). Use the answer for later rebuilds.

## Closure fold

At plan closure, when the workspace has a delta, ask the owner to confirm the fold. On a yes:

1. Call `fold(base, delta, revision, commit=..., date=...)` with the closing revision, commit and date, and
   write the result to `.tackle/map/architecture.json`. `verified_at` moves to that revision.
2. The `done` changes are now in the base. The `planned` changes stay out. Report each one, with its task,
   to the owner.

Without a yes, write nothing. The delta stays in the workspace.
