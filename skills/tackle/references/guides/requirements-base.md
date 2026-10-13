# Requirements base — depth for the [PLAN card](plan-card.md)

A project may keep its required behavior in a requirements base that outlives each plan. The base is `docs/requirements/`, one Markdown file per domain.

## Location

Before the first requirements delta in a project, ask once whether `docs/requirements/` is gitignored.
Record a yes as the `.gitignore` line and a no as a decision in the workspace, and reuse that answer in later plans.

## The delta

A plan that adds, changes or retires required behavior writes `<workspace>/requirements-delta.md` from `../requirements-delta.tmpl.md`.
Validate the delta before Ready of any task that owns an entry; validation reports every problem, and an invalid delta blocks those tasks.
Running the [recipe](../recipes/requirements-base.md) needs the owner's explicit request; without it, check each entry by reading.

## Closure fold

At closure, fold only done entries whose every scenario Check passed on the final revision, and only after the owner confirms.
List every other entry as unreconciled; the owner may run its check, correct the entry to state the shipped behavior, or leave it out.
Tackle deletes nothing from the base: a removed requirement moves under `## Retired` with the plan, the date and the reason.

## No base yet

A project without a base is valid; never offer to document the whole system, and never write a base outside a confirmed fold.

## Base format

One Markdown file per domain: `docs/requirements/<domain>.md`, `<domain>` matching `[a-z0-9][a-z0-9-]*`. The file starts `# Requirements — <Domain title>` and holds `## Active` and `## Retired`. Each requirement is a level-3 heading `### REQ-<DOMAIN>-NN · <title>`. `<DOMAIN>` is the upper-cased domain; NN has two or more digits; the id is unique across the base. The heading is followed by one statement paragraph containing `SHALL` or `MUST`, then one or more scenarios in the grammar of the Scenarios section. A retired requirement moves under `## Retired` with a line `Retired: <plan slug> · <YYYY-MM-DD> · <reason>`; Tackle deletes nothing from the base.

## Delta format

A plan that adds, changes or retires required behavior writes `<workspace>/requirements-delta.md` (shown indented here; the file itself starts each line at column one):

```markdown
  # Requirements delta — <plan title>

  Base revision: <commit or "none">

  ## ADDED
  ### REQ-<DOMAIN>-NN · <title>
  Task: T-0N · State: planned
  <statement and scenarios>

  ## MODIFIED
  ### REQ-<DOMAIN>-NN · <title>
  Task: T-0N · State: planned
  <complete new statement and scenarios>

  ## REMOVED
  ### REQ-<DOMAIN>-NN · <title>
  Task: T-0N · State: planned
  Reason: <why>
```

Empty sections may be omitted. `State` is `planned` until the owning task is Complete, then `done`.
In a multi-repo workspace each entry also carries `Repository: <id>` (see the multi-repository workspace section of `scaffold.md`). MODIFIED carries the complete replacement, never a partial diff.

## Validation problems

`validate(base, delta)` returns every problem, never only the first:

- ADDED id already active or retired in the base, or repeated in the delta → `duplicate`;
- MODIFIED or REMOVED id not active in the base → `unknown`;
- the same id in two sections → `conflict`;
- a malformed heading, missing `Task:`/`State:`, a statement without `SHALL`/`MUST`, or an entry
  with no scenario (ADDED, MODIFIED) → `malformed`;
- a scenario without a `Check:` line (see Scenarios) → `unchecked`;
- in a multi-repo workspace, an entry without `Repository:` or naming an undeclared id → `repository`.

An empty problem list is the only valid result. PLAN validates the delta before Ready of any task
that owns a delta entry; an invalid delta blocks those tasks. Running the recipe needs the owner's
explicit authorization under the recipe consent rule: an explicit requirements-delta or validation
request grants it for that validation. Without it, PLAN checks each entry against the rules above by
reading the base and the delta, and reports every problem it finds; the fold's yes (see Closure fold) runs the
recipe.

## Scenarios

A scenario is:

```markdown
#### Scenario: <name>
- WHEN <condition>
- THEN <observable result>
- Check: `<command and its pass condition>` | review: <named rubric> by <reviewer role>
```

Optional `- GIVEN <state>` precedes WHEN; `- AND` continues WHEN or THEN. `Check:` is mandatory and
names either a runnable command with its pass condition or a named review rubric and reviewer role,
per convention 5. The same grammar is a valid form for rows of a task's Case matrix and the plan's
Behavior table: a WHEN/THEN row with an empty Check cell is a readiness finding (Step 6.75), never
accepted as prose. Tables in the existing column form remain valid; the grammar is an alternative,
not a mandate.
