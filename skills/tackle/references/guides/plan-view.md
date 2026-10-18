# Plan view

The plan view is one local HTML page that shows a workspace: its task graph, requirement coverage,
decision log, newest State snapshot and the role runs that work now. It reads the board, plan, briefs,
decisions, questions, history and `resource-usage.md`.

## Request

A request such as "show the plan view" or "mostrá la vista del plan" asks for it, in any language: its own
request, not a STATUS mode, and STATUS never writes the view.
STATUS runs no script for the view and never checks it: STATUS stays read-only and code-free.

An explicit request creates the view and stands for its workspace. The owner can end that standing
request at any time by saying stop.

At a Coordinated handoff, PLAN offers the view once and names the plan-view script in the offer; only the
owner's yes builds it. That yes is the plan-view request: it is the owner's explicit authorization for the
script, the feature-request grant of [script consent](../../scripts/README.md#consent), and it stands as the
view request above. A yes also writes the curated summaries the page reads, `view/summary.json` (outcomes,
milestones and task lines) and `view/export-summary.json` (for the PDF), each declaring the board states it
describes. A no writes nothing. The host shows the page when it can display a local file.

## Rebuild

Under the standing view request, the coordinator rebuilds an existing view after every write to a page input, in PLAN
and in RUN. Under that request it rebuilds at the end of the step that wrote the input, and after each role start or finish.
The page inputs are `task-board.md`, `plan.md`, `decisions.md`, `questions.md`, `history.md` and `resource-usage.md`.
They also include the workspace `AGENTS.md` and `readiness.md`, every declared brief and `map-delta.json`.
The curated summaries, the map base, the template and the two scripts, `plan_view.py` and `architecture_map.py`, are page inputs too.
The coordinator rebuilds only a view that already exists.

Under the standing view request, the coordinator runs the plan-view script with `--check` at the end of each step
that wrote a page input. That request is the owner's explicit authorization for these checks and rebuilds. Under
that request, the coordinator rebuilds when the check says stale. The standing request covers these checks and rebuilds until the
owner says stop. After stop, nobody runs the check.

The coordinator updates `view/summary.json` and `view/export-summary.json` before a rebuild that follows a
change to task rows or states. It updates their time-bound prose, their declared board states and their as-of times.
It removes prose that it cannot update honestly. A rebuild after a role start or finish needs no summary update. Its export prose follows the reader rule in Shared presentation and PDF.

An open view reloads itself after
a rebuild, keeping its selection, filter and reading position: the build writes a small stamp script beside
the page, which the page rereads every few seconds, with no server and no process to stop. It reloads
only when opened from its file in a browser; a host view that shows a snapshot cannot update, and the page
says so with a notice. The coordinator never starts a server or background process to show the view; the stamp reload is
the way to keep an open view current. When a rebuild is
refused, the coordinator reports the refusal lines to the owner, and the earlier view keeps its earlier build
time.

## Build

Running the script needs the owner's explicit authorization; an explicit plan-view request grants it for that request ([script consent](../../scripts/README.md#consent)). Prefer an equivalent harness capability. With that authorization, run [`<skill>/scripts/plan_view.py`](../../scripts/plan_view.py) with the [template](../plan-view.template.md), where `<skill>` is the installed skill folder:

```sh
python3 -I <skill>/scripts/plan_view.py --template <skill>/references/plan-view.template.md <workspace> <workspace>/plan-view.html
```

The script imports `architecture_map.py` from its own folder; nothing is copied or extracted.

When `.tackle/map/architecture.json` exists, pass `--map .tackle/map/architecture.json` before the
workspace, with `--map-scope all` or, for a [large project](architecture-map.md#large-project), the scope the owner chose
when asked before the first build.
Without that file, pass no `--map`.

Exit 0 writes the view, exit 1 refuses and writes no file, exit 2 reports a usage error. The script uses only
the standard library, makes no network access and writes only the output file.

The page records one sha256 for each input and one overall digest. With `--check` and the build's arguments, the
script compares them with the inputs now and writes nothing. It prints `view current` and exits 0. Otherwise it
prints `view stale:` with the changed inputs and exits 1. A page without digests is stale. A usage error exits 2.

## Pre-flight

The script refuses to write when the sources disagree, printing one `refused:` line for each problem:

- a board with no task rows, or a duplicate task id;
- a dependency on an unknown task, or a dependency cycle;
- a missing brief;
- a status outside the board's vocabulary;
- with `--map`, a base that cannot be read, or a map delta that the [architecture map](architecture-map.md) script
  rejects.

## Architecture map

With `--map <base>` and `--map-scope all|changed`, the view also draws the [architecture map](architecture-map.md)
twice, today and after the plan, from `<workspace>/map-delta.json`, each picture with Cards and Diagram
tabs. Without `--map`, the page holds no map and its data island says `"map": null`.

## Focused plans

A Focused plan has a `Gate: Lite` line and no board. The script reads its requirement ids from the
`Purpose / requirements` line of the Lite plan body, or from a criteria table, and its checks from the
`Cases → checks` line. The view lists them, says the plan has no board and draws no graph. When the plan
names no requirement id, the script refuses with the Focused reason; it invents no board.

## The page

- The page itself draws the graph, in stage bands; a stage is a column, not an order of work. The script
  orders the cards with a bounded search so lines cross few times; a long arrow passes through the bands
  between its ends. It needs no network. A click opens a task; the trace buttons follow
  what the task needs and what it unblocks.
- Status filters, the coverage table and the decision log work with the same data.
- The page marks the tasks a role run works on now and lists every open run: one whose `start` row has no
  `finish` or `observe-incomplete` row.
- The page names a running role `Live`, or `En marcha` on a Spanish page, so the badge never reads like the
  In progress state.
- A Waiting on you section lists open questions from `questions.md` with their Determines line. It also lists tasks
  that are Waiting on owner or Blocked, with their Verification cell, and Open board obligations with owner and trigger.
  A question is open unless its state carries 🟢 or ✅. When nothing is open, one line says so. A Focused plan
  shows its open questions only, and the PDF report keeps its own obligations table.
- The footer shows the build time and the Methodology version of the workspace.
- The page escapes every workspace string; no workspace text runs as script.
- The interface has English and Spanish text. The script picks Spanish only on clear Spanish evidence in the
  plan; any other plan gets English, and `lang` says `en`.
- A light and dark toggle and the embedded Outfit font with a system fallback keep the page local. Motion stops under
  `prefers-reduced-motion`.

## Shared presentation and PDF

Full and Focused views use the same template and export a self-contained executive presentation of the
plan, its current progress or both. The page retains detailed requirements, task records and the full
decision archive. The complete technical plan, including code and later sections, stays in `plan.md`.

Choose a scope in the PDF controls and select Export PDF; in the browser's native print dialog, choose
Save as PDF. The view needs no network, external assets or additional runtime dependency. Each document names the
plan, its scope and build time and includes context for a reader unfamiliar with it.

- Plan presents the purpose, expected benefits, scope, work stages and key current choices.
- Progress includes context, board-derived completion and state counts, achievements, remaining work and
  next steps. A Focused plan uses its recorded State and a validation-presence cue without inventing a
  task board, measured result or completion percentage.
- Both combines the plan and progress in one presentation with one shared context and header.

Optional `view/export-summary.json` supplies typed reader-facing narrative. Status aggregates always come
from the current board. Without curation, the report uses a concise source-derived context and truthful
fallback. For a Full plan, a curated summary records the board it describes: `as_of` and `board_states` in `view/summary.json`, and
`authority.as_of` and `authority.canonical_states` in `view/export-summary.json`. When the current task states
differ, its status prose (now, next, you; achievements, open work, dependency, next steps, evidence) is set
aside with a visible note, and the canonical records speak alone until the summary is updated. The Progress and Both reports of the PDF carry the same note. The build and its check also name, on stderr, each task whose state differs from the states a summary declares. The build warns about
a summary that declares no board, since its prose cannot be checked. The report is independent of screen filters, theme and collapsed sections. The export is read by people who do not know the plan, so its prose names no task, decision, question or requirement ids, file paths, backticks or workspace names. The build warns on stderr for each field that contains one and never fails.

The light A4 report uses readable sections and wrapping text. The page restores its title, temporary
print attributes and focus after printing, cancellation or a print exception. Ordinary browser print uses
Both; native dialog, pagination and PDF destination behavior depend on the owner's browser.

## Publishing

The view stays local. Tackle never publishes, uploads or sends it.

## Auxiliary pages

When a plan view exists, an authorized auxiliary page for the plan, such as a proposals, comparison or review page, uses the plan view's visual base by default without a question about style, built with the plan-view script's page mode.

The script writes the page from the plan view's marked base in the template, with the command below. The fragment is the page's HTML body, written for the page, with no `<html>`, `<head>` or interface stylesheet. The page takes the plan's language, its title (or the fragment's first heading), the plan view's top bar and theme toggle, its typography, colors, spacing and both themes, and it shares the theme choice the plan view stores.

Give the page's heading the plan view's section markup: a `<header class="sec-head">` holding an optional `<p class="kicker">`, an `<h2>` and a `<p class="sec-lede">`, as the plan view's sections do. The base styles these classes, so the heading reads like the view's section headings. The page's `<title>` comes from the fragment's first `<h1>` if it has one, and otherwise from the plan title.

```sh
python3 -I <skill>/scripts/plan_view.py --template <skill>/references/plan-view.template.md --page <fragment.html> <workspace> <output.html>
```

Add `--check` before the paths to compare the page with the workspace and the fragment without writing anything; the output is `view current` or `view stale: <inputs>`. The page mode needs a built `plan-view.html` in the workspace and refuses, with exit 2, an output path that is the plan view itself. A page records its template, its script and its fragment, so a later change to the plan's title or language does not mark the page stale; rebuild the page on request.

Product samples, such as game palettes, sprites, screenshots and design alternatives, go inside an element with the class `tk-sample`. The base never selects that class, so a sample keeps its own appearance in both themes. Inherited text color and font still reach a sample that declares none, so sample content declares its own colors and fonts.

Without script authorization the agent writes the page itself: it copies the CSS between the `tackle-base` markers (every range, in order) verbatim from the installed template, and copies the theme script between the `tackle-base-theme` markers verbatim inside `(function () { 'use strict'; … })();`, as the script does. The brand and toggle markup come from the template's top bar in its html block, not from memory. It records the template's sha256 in a `tackle-base-digest` meta. The narrow top bar shows the brand and the toggle only; the plan view's stacked bar and its section index are not part of the base. Printing an auxiliary page is not covered.

An existing auxiliary page moves to the base only when the owner asks for it. An explicit owner preference for a page's style overrides the default and is recorded with the page. The script consent rules are unchanged: the owner's explicit request that names the page is the feature request that grants the script for that page, while a page the agent proposes and the owner merely accepts is not.

## Diagram export

Each diagram the page draws, the task graph and each architecture picture, offers its Mermaid text to copy or download; the page never renders Mermaid and loads nothing. Download saves `tasks.mmd`, `architecture-today.mmd` or `architecture-after.mmd`. A Focused plan has no task graph and so draws no Mermaid text for one.

## Sibling workspaces

A dependency on a sibling workspace's task is drawn as an external node with the sibling's name and that task's state; it has no inspector. When the sibling has a `plan-view.html`, the node and the task's line in the stage list link to that task in the sibling's view (`../<name>/plan-view.html#task-<id>`); otherwise they stay plain.

When the plan declares siblings, the page header lists them under "Sibling plans", in declaration order: each with its slug, its Relation cell and its progress as `<done> of <total> tasks complete`, read from the sibling's board. An entry links to the sibling's `plan-view.html` when that file exists; otherwise it says the sibling has no plan view yet, and nothing links. The printed reports list the siblings too, with each link target as text. A plan without siblings shows no block. The sibling boards and whether each sibling's view exists are page inputs, so `--check` reports the view stale when either changes.

A plan declares its sibling workspaces in `AGENTS.md`, under `## Sibling workspaces`, in a table whose header row is `| Sibling | Path | Relation |`. A sibling's path is `docs/plans/<name>`; only declared siblings resolve. A dependency on a sibling's task is written `T-<digits> [<slug>]` in a Depends on cell. The view refuses these cases, in board order:

- `task <id> depends on <ref> [<slug>], but no sibling named <slug> is declared`
- `task <id> depends on <ref> [<slug>], which is not on the sibling's board`
- `sibling <slug> has no tackle-workspace/5 task-board.md at docs/plans/<name>`, printed once for each sibling

A sibling's files are read only. A Brief cell may name a sibling's brief as `../<name>/tasks/<file>`; a path that leaves the sibling's `tasks/` folder keeps the refusal `brief <path> for task <id> is outside the workspace`.

## Initiative view

- `--initiative` writes one page over the workspace and the siblings it declares, one hop; `--template` stays required, and `--initiative` takes no `--page`, `--map` or `--map-scope`.
- Members are read only; a sibling's own declaration that names a workspace outside the initiative prints `outside the initiative: <slug>` once on stderr and is not followed.
- Tasks are keyed `<key>:T-NN`: the root's key is its folder name, and a sibling's key is the slug the root declares for it.
- A member with no `tackle-workspace/5` board is refused once, the root included, with the line above; a cycle across members is refused as `cycle across workspaces: <a> -> ... -> <a>`.
- `--initiative --check` prints `view current` or `view stale: <keys>` with the single-page exit codes; its keys cover each member's `task-board.md`, `plan.md`, `AGENTS.md` and each brief its board names.
- An initiative-view request is its own owner request and the owner's authorization for the script for that request; it does not add or remove scope relative to the single-workspace request.
