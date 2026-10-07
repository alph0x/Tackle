# Plan view

The plan view is one local HTML page that shows a workspace: its task graph, requirement coverage,
decision log, newest State snapshot and the role runs that work now. It reads the board, plan, briefs,
decisions, history and `resource-usage.md`.

## Request

A request such as "show the plan view" or "mostrá la vista del plan" asks for it, in any language. It
is its own request. It is not a STATUS mode, and STATUS never writes the view.

An explicit request creates the view and stands for its workspace. The owner can end that standing
request at any time by saying stop.

## Rebuild

When a view exists for the workspace, the coordinator rebuilds it after each board status change and after
each role start or finish, while the plan is worked; the standing request covers these rebuilds until the
owner says stop. The coordinator rebuilds only a view that already exists. An open view reloads itself after
a rebuild, keeping its selection, filter and reading position: the recipe writes a small stamp script beside
the page, and the page rereads it every few seconds, with no server and no process to stop. When a rebuild is
refused, the coordinator reports the refusal lines to the owner, and the earlier view keeps its earlier build
time.

## Build

Save the [recipe](../recipes/plan-view.md) as a file and run it with the [template](../plan-view.template.md):

```sh
python3 -I plan-view.py --template plan-view.template.md <workspace> <workspace>/plan-view.html
```

Exit 0 writes the view. Exit 1 refuses and writes no file. Exit 2 reports a usage error. The recipe uses only
the standard library, makes no network access and writes only the output file.

## Pre-flight

The recipe refuses to write when the sources disagree. It prints one `refused:` line for each problem.
The problems are:

- a board with no task rows, or a duplicate task id;
- a dependency on an unknown task, or a dependency cycle;
- a missing brief;
- a status outside the board's vocabulary;
- with `--map`, a base that cannot be read, or a map delta that the [architecture map](architecture-map.md) recipe
  rejects.

## Architecture map

With `--map <base>` and `--map-scope all|changed`, the view also draws the [architecture map](architecture-map.md)
twice: as the project is today, and after the plan. It reads `<workspace>/map-delta.json`, and each picture has
a Cards tab and a Diagram tab. Without `--map`, the page holds no map and its data island says `"map": null`.

## Focused plans

A Focused plan has a `Gate: Lite` line and no board. The recipe reads its requirement ids from the
`Purpose / requirements` line of the Lite plan body, or from a criteria table, and its checks from the
`Cases → checks` line. The view lists them, says that the plan has no board and draws no graph. When the plan
names no requirement id, the recipe refuses with the Focused reason. It invents no board.

## The page

- The graph is drawn by the page itself, in stage bands. A stage is a column, not an order of work. The recipe
  orders the cards with a bounded search, so the lines cross few times. A long arrow passes through the bands
  between its ends. It needs no network. A click opens a task, and the trace buttons follow
  what the task needs and what it unblocks.
- Status filters, the coverage table and the decision log work with the same data.
- The page marks the tasks that a role run works on now, and it lists every open run. A run is open
  when its `start` row has no `finish` or `observe-incomplete` row.
- The page names a running role `Live`, or `En marcha` on a Spanish page, so the badge never reads like the
  In progress state.
- The footer shows the build time and the Methodology version of the workspace.
- The page escapes every workspace string. No workspace text runs as script.
- The interface has English and Spanish text. The recipe picks Spanish only on clear Spanish evidence in the
  plan. Any other plan gets English, and `lang` says `en`.
- A light and dark toggle and the embedded Outfit font with a system fallback keep the page local. Motion stops under
  `prefers-reduced-motion`.

## Shared presentation and PDF

Full and Focused views use the same template and export a self-contained executive presentation of the
plan, its current progress or both. The page retains detailed requirements, task records and the full
decision archive. The complete technical plan, including code and later sections, stays in `plan.md`.

Choose a scope in the PDF controls and select Export PDF. The page opens the browser's native print dialog;
choose Save as PDF there. The view needs no network, external assets or additional runtime dependency.
Each document names the plan, its scope and build time and includes context for a reader unfamiliar with it.

- Plan presents the purpose, expected benefits, scope, work stages and key current choices.
- Progress includes context, board-derived completion and state counts, achievements, remaining work and
  next steps. A Focused plan uses its recorded State and a validation-presence cue without inventing a
  task board, measured result or completion percentage.
- Both combines the plan and progress in one presentation with one shared context and header.

Optional `view/export-summary.json` supplies typed reader-facing narrative. Status aggregates always come
from the current board. Without curation, the report uses a concise source-derived context and truthful
fallback. The report is independent of screen filters, theme and collapsed sections.

The light A4 report uses readable sections and wrapping text. The page restores its title, temporary
print attributes and focus after printing, cancellation or a print exception. Ordinary browser print uses
Both. Native dialog, pagination and PDF destination behavior depend on the owner's browser.

## Publishing

The view stays local. Tackle never publishes, uploads or sends it.

## Optional loopback live view

For a page served by a local producer instead of the file, save the fenced block in
[`../recipes/plan-view-live.md`](../recipes/plan-view-live.md) as `plan-view-live.py` beside the extracted
`plan-view.md` recipe; pass that source explicitly with `--recipe` so the producer never discovers a recipe by adjacency. Run it with the same workspace, template and optional map inputs:

```sh
python3 -I plan-view-live.py --template plan-view.template.md --recipe plan-view.md [--map .tackle/map/architecture.json] <workspace>
```

The producer binds only to `127.0.0.1`, answers only requests addressed to `127.0.0.1:<port>` (open that address, not `localhost`), and serves only `/` (the generated HTML) and `/health`. It rejects
query strings and every other path. On each request it hashes the declared public inputs—`plan.md`,
`task-board.md`, `decisions.md`, `history.md`, `resource-usage.md`, the supported summary files,
`map-delta.json`, declared task briefs, workspace `AGENTS.md` / `readiness.md`, the template, the plan recipe, the architecture-map recipe and the optional explicit map—and regenerates the page when those inputs change. A
failed refresh keeps the last successful page and reports an unhealthy `/health`; it never calls that page
live. The page remains file mode when the ordinary recipe is used. Theme, filter and task selection state
belongs to the page's session storage and can be restored by the parent controller after a refresh.
