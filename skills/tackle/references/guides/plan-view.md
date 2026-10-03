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
each role start or finish. The coordinator rebuilds only a view that already exists. The standing request
covers these rebuilds until the owner says stop. When a rebuild is refused, the coordinator reports the refusal
lines to the owner, and the earlier view keeps its earlier build time.

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
- a status outside the board's vocabulary.

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
- The footer shows the build time and the Methodology version of the workspace.
- The page escapes every workspace string. No workspace text runs as script.
- The interface has English and Spanish text. The recipe picks Spanish only on clear Spanish evidence in the
  plan. Any other plan gets English, and `lang` says `en`.
- A light and dark toggle and the system font stack keep the page local. Motion stops under
  `prefers-reduced-motion`.

## Publishing

The view stays local. Tackle never publishes, uploads or sends it.
