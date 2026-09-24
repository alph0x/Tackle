# Retro — initiative retrospective

Triggered by `retro [initiative]` or a natural phrase like "retro" / "how did it go". Retro
is optional: run it at initiative close or on demand as a clearly labelled partial retro. It does
not replace RUN closure or create an autonomy loop.

**Principle: detection before judgment.** Mine `task-board.md` + `history.md` by grep/count first; use judgment only to distill the counts into lessons. For an unindexed archive, mining reads `history-archive.md` then `history.md` in a new workspace, or `log-archive.md` then `log.md` in a historical workspace. For indexed segments use the validated chronological archive index from `context-lifecycle.md`, then the active history; never count checkpoints or summaries as original events. Missing/corrupt history makes affected metrics unavailable, never zero. Read-only over the selected task board, history and `decisions.md`; the only writes are `docs/plans/<initiative>/retro.md` (instantiated from `references/retro.tmpl.md`) and one entry in the selected history.

## Metrics — mined, not remembered

Every metric carries a copy-paste recipe; the recipes live in the template's Metrics table. What each one measures:

- **Tasks by status** — count exact task rows and their Status field in `task-board.md`, using its declared schema.
- **Attempts over budget** — count `attempt N:` journal lines per task in `history.md` against the attempt budget declared in the workspace `AGENTS.md`.
- **Blocked durations** — dates between the log entry that marks a task Blocked (legacy ⏸) and the entry that unblocks it.
- **Reopened tasks** — `Complete → In progress` or legacy `🟢 → 🟡` transitions in `history.md` (regression-sweep reopenings included).
- **Comprehension debt** — tasks recorded Complete (legacy 🟢) with no human review recorded in the log: mechanically done, humanly unread. High comprehension debt is a warning even when the board is all green.
- **Gate accuracy** — the gate recorded at intake vs actual effort (tasks executed, sessions spent): Full-gate initiatives closed in ≤ 2 sessions are over-planning candidates; Lite-gate ones spanning 3+ sessions are under-planning candidates.
- **Exact-token coverage** — measured/eligible by metric and comparable scope, with `n/a` rows visible before any arithmetic.
- **Coverage-gated totals** — cohort totals and rankings only after 100% comparable coverage; otherwise report labeled observations and suppress the aggregate.
- **Coverage-gated recommendations** — tier/effort recommendations only after 100% coverage plus at least three like-for-like completed runs.
- **History growth** — lines per `history.md` session entry (recipe in `retro.tmpl.md`): resume cost compounds across every future session, unlike execution cost which is paid once per task; a rising trend routes narrative back to `decisions.md`/`reference-docs/`.

## Lifecycle-first coverage

Read the v2 ledger before any token arithmetic. For every metric and comparable scope, print
`measured/eligible` plus a percentage; no eligible rows are shown as `0/N (0%)`, never as a
zero-over-zero denominator. Duration, attempts, rework, incomplete runs, verification outcomes,
and task time-to-green remain useful when exact telemetry coverage is 0%.

- At 0% exact-token coverage, report `0/N (0%)` and suppress token totals, shares, rankings, and
  recommendations.
- Partial exact coverage may list labeled observations, but totals and rankings require 100%
  comparable coverage; mixed role/session scopes remain separate and unjoined.
- Tier/effort recommendations require 100% coverage, identical scope/source/semantics, and at
  least three completed like-for-like runs; otherwise label the result a hypothesis.

### Fixture recipe

Run `awk 'BEGIN{FS=sprintf("%c",124)} {m=$2; sub(/^[[:space:]]+/,"",m); sub(/[[:space:]]+$/,"",m); r=$6; sub(/^[[:space:]]+/,"",r); sub(/[[:space:]]+$/,"",r)} (m=="duration") + (m=="attempts") + (m=="rework") + (m=="verification") + (m=="tokens") {print m " " r}' resource-usage.md` from a fixture workspace. The four fixtures under
`eval/fixtures/usage-observability/` are the reference cases: zero prints `0/N`, partial and
mixed suppress aggregates, and full alone permits expected totals and recommendations.

**Lite plans** (no `task-board.md`): the retro still runs — board-derived metrics report `n/a`; log-derived ones stand.

## Cost analysis

Mined from the exact-token recipe only after the coverage gate, never remembered; report the
`n/a`-row counts alongside any permitted totals. Report `n/a` for the whole section when the
workspace has no `resource-usage.md`. `resource-usage.md` remains the only ledger source; unexposed harness fields
stay `n/a`, never estimated.

### Conclusions

- **Top-consuming tasks vs their bindings** — only within a 100%-covered comparable cohort, rank permitted exact totals by task and compare each against its bound tier/effort.
- **Phase shares** — only within a 100%-covered comparable cohort, compare permitted PLAN / EXEC / RETRO totals; otherwise report the coverage gap instead of a share.
- **Cache-write-weighted cost** — where the harness exposed cache splits, a task heavy on `cache_write` vs `cache_read` cost more under the billing split (writes ≈ 1.25× reads); rank by `cache_read`/`cache_write` parity, not by input+output throughput alone.

### Recommendations

- **Downgrade candidates** — tasks whose actual work matched a lower tier/effort than bound (few tokens on an expensive binding): propose the cheaper binding for the next plan of that shape.
- **Recurring shapes worth re-defaulting** — shapes that consistently consume above or below their role default effort: candidates for the role→effort defaults in `team.md`.
- **Duration outliers vs bound effort** — tasks whose `duration_ms` sits well above their bound effort's norm (or `compactions`/`context` spikes) are candidates for re-binding or re-decomposition; a long, compacting task bound `low` signals under-scoped work.

## What worked / what didn't / lessons

Distill from the metrics plus the Decisions and Blockers sections of the log. One line each. A lesson must be actionable by a future plan ("gate X earlier", "the attempt budget was too low for tasks shaped like Y"), not a platitude.

<a id="profile-candidates-learning-loop"></a>
## Preferences and lessons candidates (profile learning loop)

The learning loop is the only mechanism that lets Tackle adapt to a user or project. It is opt-in,
per scope, and never silent. Lessons must identify an observed cause and a future action; an
unsupported opinion does not become a global rule.

### Opt-in (asked once per scope)

At the first learning opportunity, ask per scope:

- **Both scopes** if neither `~/.tackle/user-profile.md` nor `.tackle/profile.md` exists.
- **Project only** if the user profile already exists and is enabled.

A "no" writes the disabled stub (`Evolution: disabled (YYYY-MM-DD)`) in the relevant profile file and is never re-asked. The user can flip it later by enabling evolution or deleting the file.

### Distilling candidates

Mine the following sources during retro:

- `decisions.md` deltas vs recommended defaults (recurring overrides).
- `history.md` attempt-journal lines that exceed the budget or show no-progress.
- Reopened tasks (`🟢 → 🟡`) in `history.md`.
- Escalation packets from `history.md`.
- `verify` findings that recurred across tasks.

Present candidates as a batch. Each candidate must include:

- A hypothesis or directive entry.
- The supporting evidence count.
- A proposed confidence (0.0–1.0).

### Confirming and writing

Everything is batch-confirmed by the user before writing. Never append to a profile without an explicit "yes".

For each separately confirmed candidate:

- Update counters from intake tally lines: `profile proposals: N accepted, M overridden (<which>)`.
- Accept ⇒ increment ✓; override ⇒ increment ✗.
- If ✗ ≥ 3 with confidence < 0.3, set `status: retired` (kept, never deleted).
- If a project hypothesis is confirmed in ≥ 2 repos, propose promoting it to the user profile (ask again).

### Directives

Propose retirement or supersession of incompatible hypotheses without rewriting history. Intake already excludes them from defaults; pending cleanup does not block implementation. One isolated observation remains a hypothesis, not a mandatory global rule.

Recurring failure evidence may propose a `directive:` entry (C-20). A directive targets a named template or guide section and is considered at instantiation only when applicable and compatible with the current authority order. Project directives outrank user directives. A directive whose target section no longer exists is flagged **stale** for re-confirm-or-retire. When the failure evidence is a repeatable mid-session action (a commit message, a push, a release step), distil the directive with an `applies_to:` tag naming that action moment — instantiation-time application never reaches an action taken 30 sessions after intake (taptopaykit-integration A1: a commit-format directive written session 23, violated session 35).

### Opt-out anytime

The user can stop evolution at any moment, per scope, with any phrasing. Two modes:

- **Pause**: flip the header to `Evolution: disabled (YYYY-MM-DD)`. Counters are kept; re-enabling resumes them.
- **Purge**: delete the profile file entirely. The next learning opportunity may re-ask for opt-in.

Both take effect immediately.

<a id="plan-archetype-candidates-learning-loop"></a>
## Plan reference plan candidates (learning loop)

At initiative close, consider whether the plan itself is worth distilling into `references/archetypes/` (format: `references/archetypes/README.md`).

### Eligibility

Offer extraction only when **the decomposition held**: no major replans and no D-xx rewrites of the task/edge graph after intake — tasks closed against the graph that was planned. A plan that was substantially re-shaped mid-flight has no stable skeleton to distill; skip without asking.

### Extraction template

One reference plan file per skeleton: `references/archetypes/<name>.md` with the sections the README fixes — name + one-line summary, task list, edge pattern, wave shape, trap warnings, provenance (this initiative, retro link). Mine the graph from `plan.md`/`task-board.md`; mine trap warnings from attempt journals and reopened tasks; judgment only names and summarizes.

### Confirming and writing

Everything is batch-confirmed by the user before writing — present the reference plan candidate alongside the profile-candidate batch, never write it silently. Only the `retro` workflow writes reference plans.

## Where results go

- `retro.md` in the initiative workspace, one per initiative (a partial retro overwrites the previous partial; the close retro is final).
- One `history.md` entry noting the retro ran, with the Metrics values as its evidence.
- One `references/archetypes/<name>.md` per batch-confirmed reference plan candidate (the only write outside the initiative workspace).
- Report the useful findings and pending consent concisely per the communication contract — link to `retro.md`, don't paste it.
