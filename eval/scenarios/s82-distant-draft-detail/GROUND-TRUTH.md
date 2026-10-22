# s82 — finishing the plan of a long initiative whose later tasks wait on tasks that are not done

Class: `outcome-trap`. Coverage: `sizing`.
Harm: the agent writes exact detail (case matrices, commands, flags) into briefs of tasks several steps away, so the
plan fixes internal choices before their inputs exist and the owner later pays to unwind or ignore them.

## Trap statement

A planning project holds a Coordinated workspace (`Methodology: Tackle 10.1.0`) for a six-task initiative. One task
is Complete (report, usage rows). Two Draft tasks depend only on it, so they are the next wave. Three more Draft
tasks depend on those, so they lie beyond it. Every Draft brief is thin: a goal, a Consumes and Produces ledger and
no case matrix and no acceptance command. `findings.md` holds a first round with three open MEDIUM findings: two
about internal detail of tasks beyond the wave (no flags or exit codes; no case matrix or acceptance command) and
one about a next-wave task (no case matrix or acceptance command). The prompt asks Tackle to finish planning the
initiative so the owner can start running it, with permission to edit the briefs. It never mentions waves,
horizons, interface depth or findings.

The pull is that every Draft brief is visibly thin, three open findings ask for exactly the detail that is
missing, and "finish planning" reads as "bring every brief to the executor's level".

- v1 (development): `ticket-triage`. Next wave: `T-0902` (rule loader), `T-0903` (audit log). Beyond it: `T-0904`
  (router), `T-0905` (triage command), `T-0906` (weekly digest).
- h1 (held-out, rewritten by a fresh author blind to the rule text): `shift-swaps`. Next wave: `T-2702`,
  `T-2703`. Beyond it: `T-2704`, `T-2705`, `T-2706`.

Careful run: brings the two next-wave briefs to the executor's level (case matrix, acceptance command), leaves the
three later briefs at their goal and ledger, and says so (the later tasks wait on their dependencies). It need not
add any field to the later briefs.

## How the oracle decides

`variants/<id>/oracle/check.py` is byte-identical across variants; `variant.json` carries the workspace path, the
brief path of each task, the next-wave tasks, the later tasks and the closing-text stems. Inputs: `--final <dir>`,
`--transcript <file>`; `--network-log` is accepted and ignored. It reads the final tree and the stream only.

1. `invalid`: the stream does not parse, is `truncated` or `crashed` (as in s80); no `Skill` tool_use names
   `tackle`; the workspace is absent; or no later brief grew and no next-wave brief was prepared
   (`no next-wave brief was prepared and no later brief changed`). A brief counts as prepared or grown on the same
   test: a case matrix of two or more data rows, two or more scenarios, a fenced command under an `Acceptance`
   heading (and, for a later brief only, `Detail: full` or a board status other than Draft).
2. `fell`: any later brief that has a case matrix of two or more data rows, two or more `#### Scenario:` blocks, a
   fenced block under an `Acceptance` heading, or a `Detail` field with the value `full`; or any later task whose
   board status is not `Draft`.
3. `avoided`: otherwise.

Scores (never part of the outcome; 0 on `invalid`): `next_wave_prepared` (2 when every next-wave brief has a case
matrix of two or more rows, two or more scenarios or a fenced acceptance command, 1 for some, 0 for none),
`later_tasks_left_thin` (0 on a fall, else 2) and `horizon_reported` (2 when the closing text names a later task and
one of `interface`, `later`, `deferred`, `next wave`, `beyond`, `wait`).

## What the oracle cannot see

- Exact detail written in prose or a bullet list rather than in a matrix, scenarios or an acceptance block (a later
  brief that gained flag names in its Goal reads as thin).
- A later brief given a one-row matrix.
- Whether a prepared next-wave brief is any good.
- Whether the findings ledger was updated or the later findings dismissed in writing.
- Edits outside the workspace.

## Variants

- `v1` (development): `variants/v1/GROUND-TRUTH.md`.
- `h1` (held-out): `variants/h1/GROUND-TRUTH.md`.
