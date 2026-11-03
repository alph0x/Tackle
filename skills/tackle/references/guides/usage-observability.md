<a id="usage-observability--portable-contract"></a>
# Resource usage — portable contract

This guide defines the provider-independent lifecycle ledger and the optional exact-telemetry
sidecar: a documentation contract, not a collector or executable.

## Lifecycle records

Coordinated (Full) and Focused (Lite) workspaces require `resource-usage.md`; Direct (None) creates no workspace or ledger. A Direct task
resumed inside an existing workspace preserves its existing lifecycle contract. Read this guide
only when a ledger is applicable. Use observed clock and launch metadata or `n/a`; never fabricate
midnight start times, infer model/effort from a role label, or duplicate rows to appear compliant.

New workspaces declare `Schema: tackle-observability/2` in `resource-usage.md` and use this table. The third column is `Task` in new workspaces; historical `Point` headers remain readable without rewriting their rows:

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

`Run ID` is opaque and workspace-unique; the portable default is
`<YYYY-MM-DD-sN>/<task>/<role>/<ordinal>`. `Event` is `start`, `finish` or
`observe-incomplete`. A role appends `start` before substantive work and `finish` at close. A
Coordinator may append `observe-incomplete` when a start lacks a finish; that observation time
is no claimed end and derived duration stays `n/a`.

Legal flow:

```text
absent -> start(running) -> finish(success|failed|blocked|aborted)
                         \-> observe-incomplete(incomplete)
```

Exactly one start and at most one terminal event are valid. An orphan terminal, duplicate start,
duplicate terminal, negative count, or mismatched Task/Role is invalid. Missing values are `n/a`,
never zero and never estimated. Unexposed clock or runtime metadata does not block otherwise
observable work: record metadata as `n/a` and keep the command result. An unavailable required
execution environment is an acceptance gap, not missing telemetry, and blocks its owning scope.
Tier records an observed fast/standard/frontier model binding, never the Lite/Full route.
Attempts records shared failed implementation correction-validation cycles, plus one declared
capability escalation per task, counted once as its own event, always, including on the task's first
validation; initial validation, dispatch and repeated tests of an implementation fault do not count.
For a nonzero Attempts value, Verification or Source links a task-matched failed correction-validation
record or one task-authorized declared capability escalation. A relative path and anchor, or a stable
event identifier resolving in the task history, is sufficient when the cited record gives the event
identity, fault or unavailable capability, observed result, correction or authorization, and validation.
Never substitute a count label, a path that merely exists, or an unrelated task's event for those facts.
Keep the shared count across actors; two distinct failed correction events may count two, while a repeated
test or duplicate event identifier never adds a cycle. The labels and ordering of those facts are no
new history schema. With no correction observed, record zero with the observation source; with the
history or observation unavailable, record `n/a` rather than inventing zero.
Rework uses a separately defined observed rework counter,
otherwise `n/a`. Preserve counters across actors/resumptions; zero requires observed absence.
A role outcome describes that role: a reviewer may finish successfully while reporting a blocked
product. Verification/Source identifies that scope; it cannot imply initiative completion. Outcome
contains only `running` on start, `success`/`failed`/`blocked`/`aborted` on finish, or `incomplete`
on observe-incomplete; product verdict prose belongs in Verification/Source.
Lifecycle recording never gates closure ([template](../resource-usage.tmpl.md)).
The execution sequence and correction limits are owned by the [RUN
card](run-card.md), with depth in `references/guides/run.md`.

Validation clocks describe the validation child, not the enclosing role. An executor cannot observe
its own future process termination, so its finish timestamp is `n/a` unless an external observer
supplies an actual terminal event; Source names the limitation. Never copy a test end or take a
later reconstruction clock. Product outcome and terminal-time availability are separate facts.
New Lite ledgers use the v2-only body in `../lite-plan.tmpl.md`; legacy rows are preserved only when
already present. Verification and Source index captured receipts rather than restating raw metadata.

## Optional sidecar

`resource-usage.telemetry.jsonl` contains one JSON object per observation in new workspaces;
historical `usage.telemetry.jsonl` stays readable. Both use schema
`tackle-observability-telemetry/1`. Required envelope fields are `schema`, `captured_at`,
`collector`, `source`, `scope`, `scope_id`, `run_id` when `scope=role`, `metrics` and
`provenance`. Scope is `role`, `session` or `account`; a session/account observation without exact
attribution uses `run_id: n/a`.

For Codex Desktop and `codex exec --json`, the optional literal
[native capture recipe](codex-native-usage.md) can populate this sidecar at role start and after
an externally observed close, reporting directly observed configured model/effort and a native
terminal candidate separately; only an exact Run ID/turn mapping may fill a role end. Its absence
or failure leaves telemetry `n/a` and never blocks the task.

The `metrics` object may expose any subset of `input_tokens`, `output_tokens`, `reasoning_tokens`,
`cache_read_tokens`, `cache_write_tokens`, `requests`, `tool_calls`, `compactions`,
`context_tokens`, `cost` and `currency`. Values are non-negative numbers or `n/a`; unknown and
missing are never zero. A local or API-equivalent cost is not canonical cost and must be labeled
non-comparable source data. Session/account data is never allocated, divided or delta-inferred
into a role.

## Correlation and comparison

Role-scoped sidecar observations join only on an exact `run_id`. A native provider id without an
explicit mapping stays unjoined. A reviewed launch attribute or post-hoc one-to-one mapping is
acceptable; timestamp proximity is not exact correlation. Compare only the same metric, unit,
scope, collector semantics and pricing basis; subscription cost, API cost and API-equivalent
estimates are separate bases.

The coordinator records the billed models of every role session, or `n/a` when the harness does not report them.

## Coverage and dependency boundary

Retro computes `measured/eligible` plus a percentage per metric and comparable cohort. No eligible
measurements is `0/N (0%)`, never `0/0`. Zero or partial telemetry still supports duration, attempts,
rework, incomplete runs, verification outcomes and task time to completion. Partial exact coverage may
list labeled observations but cannot produce totals, shares, rankings or tier recommendations.
Totals/rankings require 100% comparable coverage; tier/effort recommendations also require at least
three completed like-for-like runs. The universal ledger never depends on a collector; no hook,
daemon, plugin, provider API or sidecar is required for a task to close.

<a id="claude-code-native-sources"></a>
## Host-native session transcripts

Each host has its own usage records; this section describes one host. There the coordinator can fill
the sidecar from local files, with no collector or recipe. Check the installed version first: these
paths and fields can change. Copy only numbers, ids, model names and times; never copy
prompt, response or tool content.

- Each subagent dispatch returns a subagent id. Write that id in the Source of the role's finish row.
- The subagent's transcript is a JSONL file whose path the owner supplies, for example as the host
  exports it. Its `.meta.json` names the dispatch description and a model alias. Take the model from
  the assistant events, which name it in full.
- One request can appear as several assistant events with the same `message.id`. Keep only the last
  event of each `message.id`; never add up every event.
- Over those last events, add up `input_tokens`, `cache_creation_input_tokens` as `cache_write_tokens`,
  `cache_read_input_tokens` as `cache_read_tokens`, and `output_tokens`. `requests` is the count of
  distinct `message.id` values. `reasoning_tokens` is the sum of `output_tokens_details.thinking_tokens`
  when every kept event has it, otherwise `n/a`. It is part of `output_tokens`; never add it to them.
- Write one `scope: role` record with that role's Run ID as `run_id`. The join is exact, because the
  coordinator assigned both the Run ID and the dispatch.
- A subagent that served several Run IDs gives one `scope: session` record with the subagent id as
  `scope_id` and `run_id: n/a`. Never divide it into roles.
- The first assistant event time is a host-observed start clock and can fill the start `At`. Record the
  last assistant event time in `provenance` as the last observed request; it is not a finish clock.
- The coordinator's own transcript, at a path the owner supplies in the same way, gives one
  `scope: session` record, captured once at close, with its last event time in `provenance`. Never
  divide it into roles.
- Plan-limit percentages and the context-window count describe the account and the current context,
  not cumulative role usage.
- A missing, unreadable or unknown file or field stays `n/a`.

## Pre-v2 tables the migration carries

An eight-column header beginning `Point | Role | Tier | Model | Effort | Tokens in | Tokens out |
Session` is legacy and stays readable. Adoption appends the v2 marker/table below it and writes
only v2 events. Legacy rows without exact run ids stay legacy-scoped. Rollback removes only the
new v2 section and preserves legacy bytes. Migration and compatibility reads are fixture-tested.
Only a migration carries such a table into `resource-usage.md`; a new ledger starts on the v2 table.

## Negative validator example

This role-scoped object is invalid because it omits `run_id`:

```json
{"schema":"tackle-observability-telemetry/1","scope":"role","scope_id":"role-7","metrics":{"input_tokens":12}}
```

Use this dependency-free structural check for the negative example:

```sh
validate_role_record() {
  printf '%s\n' "$1" | awk '/"scope"[[:space:]]*:[[:space:]]*"role"/ {role=1} /"run_id"[[:space:]]*:/ {run=1} END {exit (role && !run) ? 1 : 0}'
}
negative='{"schema":"tackle-observability-telemetry/1","scope":"role","scope_id":"role-7","metrics":{"input_tokens":12}}'
if validate_role_record "$negative"; then echo "invalid role record accepted"; exit 1; fi
```

The validator must reject the object; a session/account object may use `run_id: n/a`. Absence of a
sidecar is valid and never a task-level failure.

`At` is a clock in the form `YYYY-MM-DDTHH:MM:SS[.fff](Z|±HH:MM)`; minute-only and space-separated clocks are unmeasured.

## Record writing and manual fallback

For an explicit plan or run request, record lifecycle, correction events, closure receipts,
history and snapshots, telemetry, and compiled clauses with `record.py` using
`python3 -I skills/tackle/scripts/record.py --workspace PATH --spec RELATIVE_JSON`.
The spec is workspace-relative JSON with schema `tackle-record/1`, a `kind` and `data`;
the six kinds are `lifecycle`, `correction`, `closure`, `history`, `telemetry` and
`compile-clause`. Supply observed facts rather than inferred values. If scripts cannot run,
write the six forms manually as described here, preserving evidence and the normal checks.

`PATH` is an existing absolute physical workspace path; the writer refuses symlink components.
It requires POSIX locking and descriptor-relative no-follow operations. If those are unavailable,
including native Windows, use the manual forms in this guide rather than weakening path checks.

The closed envelope has exactly `schema`, `kind` and `data` fields; its schema is `tackle-record/1`.
The data fields are:

- `lifecycle`: required `run_id`, `event`, `task`, `role`; optional `harness`, `tier`, `model`,
  `effort`, `at`, `attempts`, `rework`, `verification`, `source`, `outcome`; `absence` may contain
  `event_id` and an actual `observed` absence for zero. A finish may include `telemetry` with the
  envelope fields below, exactly matching the role and run.
- `correction`: `event_id`, `task`, `run_id`, `failure_id`, `observed_failure`, `correction`,
  `validation_command`, `result`.
  `Cycle count: 1` is the correction event's local increment; lifecycle Attempts carries the shared cumulative count.
- `closure`: `task`, `remains` (`none` or a nonempty list of existing `O-NN` ids), and optional
  active decision `erratum`.
- `history`: dated unique `heading`; string lists `did`, `decisions`, `blockers`, `next`;
  `state` with `task_state`, `in_flight`, `blocked_on`, `resume_from`, `checkpoint`.
- `telemetry`: `captured_at`, `collector`, `source`, `scope`, `scope_id`, `run_id`, `metrics`,
  `provenance`; use the optional-sidecar contract above.
- `compile-clause`: `clause_id` and existing workspace-relative `brief`.

The tool writes workspace records and prints paths and digests; it does not establish the truth of
the supplied facts. Unknown data stays `n/a`, never an invented zero, model, terminal time or cost.
For a tool-written lifecycle row, positive Attempts Source starts with a correction-event reference;
Verification is a reference, not acceptance prose. A finish without telemetry records availability with empty metrics and
explicit `n/a` collector and provenance; captured time is not the role's finish time.

## Correction journal

Each failed implementation correction appends an attempt-journal entry, naming the observed failure,
correction, validation command, result and cycle count, before another attempt, and re-reads the earlier
entries. A correction changing a contract or acceptance requires the authorized superseding decision
first, then re-grounding and revalidation. Each attempt-journal line takes the form `correction cycle N of 3: <failure> → <correction>; <validation command>: <result>`.
The three-cycle ceiling is the default; new records use `N of M` after an explicitly approved extension,
while historical `N of 3` entries remain exact. Historic `attempt N:` records remain history.
The structured correction event records Run ID and Failure ID first, then task, observed failure,
correction, validation command and result under its event ID; it does not invalidate other task-linked evidence forms.

## Closure and report records

The local report contains, in order: authorization and preflight; implementation and target
observation; surrounding and integration observations; correction journal and any failure packet;
deliverable acceptance; independent semantic review when required; final status and unresolved risk,
closed by the receipt. Each observation links to its immutable raw record. Raw records are
append-never/overwrite-never artifacts named with a unique Run, Task, validation ordinal and observed
timestamp. Record unknown telemetry as `n/a`; never infer duration, tokens, cost, actor,
independence or success.

The receipt ends with one `**Remains**:` line, on its own line outside any code fence: `none`, or the
`O-NN` ids the task leaves `Open`, comma-separated. Each id is also a row of the board's obligations
table and is named in the newest State snapshot; lint row 17 reads this line. A report ends like this:

```text
Final status: Complete. Next owner: the coordinator.
**Remains**: O-02
```

At closure, the Coordinator records the brief's sha256 in the report, on its own line outside any code fence, right before the final status line:

```text
**Brief sha256**: <64 lowercase hex digits of the brief file's bytes>
```

The Coordinator also appends one line, `Brief sha256 T-NN: <the same hash>`, to that task's close entry in `history.md`, outside any code fence. History only grows, so the first such line is the protected baseline: never add a second one. To repair a wrong first value, set the report's `**Brief sha256**` line to that value, then record an erratum decision and an erratum line with the true hash.

A brief whose task is Complete, Skipped or Unverifiable is a closed record. No agent edits it, fix agents included, until an erratum is recorded. An erratum is an active decision that authorizes the edit. After each authorized edit, the Coordinator appends one line to the report:

```text
**Brief erratum**: D-xx · sha256 <64 lowercase hex digits after the edit>
```

Lint row 14 compares the brief with the last erratum's hash, or with the `**Brief sha256**` value when there is none, and compares that value with the first history line of the task. It prints `rewritten brief hash` when the report's baseline differs from that history line or is missing, and then uses the history line as the expected hash. It requires the hash line only in a workspace stamped 10.2.0 or later, and a closure without a history line stays silent.

## History and snapshot records

**Append-only** history, oldest first (newest at the bottom). One terse entry per session:
`## YYYY-MM-DD · session N · <title>` with **Did / Decisions / Blockers / Next** and, at the end of the
**newest** entry, a **State snapshot** sufficient to resume without re-reading history. Never rewrite old
entries. Each entry carries what a later session needs to resume, preserving material constraints and record references, and leads with the compact block — tasks touched, decisions by D-id, status deltas, verification commands + pass/fail. Reasoning and narrative route to `decisions.md` / `reference-docs/`; the history indexes them, it never re-narrates.
Never log secrets. **The task board `task-board.md` is canonical current state; this file preserves original history.**

Failed attempts: one journal line per attempt, each with its verification block:
`correction cycle N of 3: <failure> → <correction>; <validation command>: <result>`.
New records after an approved extension use the approved total ceiling (`correction cycle N of M`);
historical entries retain their original `N of 3` wording. On budget exhaustion or no-progress
(two consecutive attempts with identical evidence output), the task becomes Blocked and the entry
carries an escalation packet: task, Attempts N (budget M), reason budget or no-progress, attempt journal
with verification blocks (last attempt at minimum), current best failure hypothesis, and the smallest
unblocking question linked to Q-xx (user-owned if applicable).

The newest State snapshot records Task state, In flight, Blocked on, Resume from and Checkpoint, and
Active obligations: every `Open` `O-NN` id from the board on one comma-separated line, `none` when
empty, followed by applicable old decisions, blockers, failure lineage and spent cycles. Never edit
an older snapshot. A resumed session appends a uniquely labelled continuation, never a duplicate
session heading. Write changed events once with stable references; do not append repeated transcripts.

**Verification entries** — every "acceptance check passed/failed" claim carries:

This block is a summary/index, never raw capture: link the exact captured command and complete
stdout/stderr/process result, never reconstructed from prose. One observation serves all covered checks.
Timestamps and model/effort come from actual observations or are `n/a`. Coordinated work uses this template;
Focused work uses its self-contained plan/history/resource-usage procedure; Direct work keeps a check summary
without instantiating it.

````
**Verification record** — `the literal command`
```
trimmed stdout/stderr (≤ 10 lines, keep counts and exit line)
```
cwd: `{{absolute cwd}}` · runtime: `{{tool/runtime or n/a}}`
start: `{{UTC timestamp or n/a}}` · end: `{{UTC timestamp or n/a}}`
exit: `{{exit code}}` · timeout: `{{true/false}}` · signal: `{{signal or n/a}}`
revisions: input/code/config/dependency/contract `{{fingerprints or n/a}}`
raw: `{{immutable raw check record path}}`
````

No verification block ⇒ the claim is an assertion, and the task may not become Complete. Keep one immutable
raw check record per validation; unknown telemetry stays `n/a`.

## Compiled clause records

Record each selected clause's id, revision and hash at compile time. Inline only applicable clauses;
never copy a whole guide or edit a compiled clause independently.

- **{{clause id}} · {{revision}} · sha256 `{{hash of the exact clause bytes}}`**: {{the
  canonical clause, copied byte-for-byte from its authoritative contract}}.

The compiler hashes the exact UTF-8 clause bytes, records the source path and hash
beside the Task, and checks the digest before execution. A clause's bytes run from its
`## <id> · <title>` heading through the line before the next `## ` heading or `<a id=` line, each
line ending in one newline; the seal check in `guides/verify.md` step 8 recomputes them. The compiler
supersedes and regenerates a changed authoritative clause; a worker never repairs a hash or clause locally.


## Template lifecycle details

`Event` is `start`, `finish` or `observe-incomplete`: append `start` before substantive work and one terminal
`finish` at role close; for a role that ends abruptly, append `observe-incomplete` when observed, never inventing
an end time or duration. `Run ID` defaults to `<YYYY-MM-DD-sN>/<task>/<role>/<ordinal>`, unique within the
workspace. Unavailable Harness, Model, Effort, Attempts, Rework and Verification values are `n/a`, never
estimated. Attempts and rework retain the shared Run counters across actors and resumptions; they never reset
for a new role or session. Lifecycle recording is informative and never gates task closure. Outcome is
`running` for start, `success`/`failed`/`blocked`/`aborted` for finish and `incomplete` for observe-incomplete.
Product acceptance prose stays in Verification/Source, even when the role finishes successfully. A positive
Attempts count needs a relative trace reference or stable event identifier for task-matched failed correction
validation or one declared authorized escalation; count labels, initial checks, dispatches and repeated tests
alone do not support it. Preserve distinct cycles across actors, counting a duplicate event only once. `0`
requires observed absence with its source; use `n/a` when support is unknown.

The report ends with a receipt: what is complete, what remains (the `**Remains**:` line), and who owns the next step.

Capture the role's observed finish clock as `finishAt`; include Run ID, or `n/a` with reason for unavailable fields.

