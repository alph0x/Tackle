<a id="usage-observability--portable-contract"></a>
# Resource usage — portable contract

This guide defines the provider-independent lifecycle ledger and the optional exact-telemetry
sidecar. It is a documentation contract, not a collector or executable.

## Lifecycle records

Coordinated (Full) and Focused (Lite) workspaces require `resource-usage.md`; Direct (None) creates no workspace or ledger. A Direct task
resumed inside an existing workspace preserves its existing lifecycle contract. Read this guide
only when a ledger is applicable. Use observed clock and launch metadata or `n/a`; never fabricate
midnight start times, infer model/effort from a role label, or duplicate rows to appear compliant.

New workspaces declare `Schema: tackle-observability/2` in `resource-usage.md` and use this table. The third column is `Task` in new workspaces; historical `Point` headers remain readable without rewriting their rows:

| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

`Run ID` is opaque and workspace-unique; the portable default is
`<YYYY-MM-DD-sN>/<task>/<role>/<ordinal>`. `Event` is `start`, `finish`, or
`observe-incomplete`. A role appends `start` before substantive work and `finish` at close. A
Coordinator may append `observe-incomplete` when a start lacks a finish, but that observation time
is not a claimed end and derived duration remains `n/a`.

Legal flow:

```text
absent -> start(running) -> finish(success|failed|blocked|aborted)
                         -> observe-incomplete(incomplete)
```

Exactly one start and at most one terminal event are valid. An orphan terminal, duplicate start,
duplicate terminal, negative count, or mismatched Task/Role is invalid. Missing values are `n/a`,
never zero and never estimated. Unexposed clock or runtime metadata does not block otherwise
observable work: record metadata as `n/a` and preserve the command result. An unavailable required
execution environment is an acceptance gap, not missing telemetry, and blocks its owning scope.
Tier records an observed fast/standard/frontier model binding, never the Lite/Full route.
Attempts records shared failed implementation correction-validation cycles; initial validation,
dispatch and repeated tests do not count. Rework uses a separately defined observed rework counter,
otherwise `n/a`. Preserve counters across actors/resumptions; zero requires observed absence.
A role outcome describes that role: a reviewer may finish successfully while reporting a blocked
product. Verification/Source identifies that scope; it cannot imply initiative completion.
Lifecycle recording is informative and never
gates task closure. The execution sequence and correction limits are owned by
`references/guides/run.md`.

Validation clocks describe the validation child, not the enclosing role. An executor cannot observe
its own future process termination. Its finish timestamp is `n/a` unless an actual terminal event
is supplied by an external observer; Source names the limitation. Do not copy a test end or take a
later reconstruction clock. Product outcome and terminal-time availability are separate facts.
New Lite ledgers use the v2-only body in `../lite-plan.tmpl.md`; legacy rows are preserved only when
already present. Verification and Source index captured receipts rather than restating raw metadata.

## Optional sidecar

`resource-usage.telemetry.jsonl` contains one JSON object per observation in new workspaces;
historical `usage.telemetry.jsonl` remains readable. Both use schema
`tackle-observability-telemetry/1`. Required envelope fields are `schema`, `captured_at`,
`collector`, `source`, `scope`, `scope_id`, `run_id` when `scope=role`, `metrics`, and
`provenance`. Scope is `role`, `session`, or `account`; a session/account observation without exact
attribution uses `run_id: n/a`.

For Codex Desktop and `codex exec --json`, the optional literal
[native capture recipe](codex-native-usage.md) can populate this sidecar at role start and after
an externally observed close. It reports directly observed configured model/effort and a native
terminal candidate separately; only an exact Run ID/turn mapping may fill a role end. Its absence
or failure leaves telemetry `n/a` and does not block the task.

The `metrics` object may expose any subset of `input_tokens`, `output_tokens`, `reasoning_tokens`,
`cache_read_tokens`, `cache_write_tokens`, `requests`, `tool_calls`, `compactions`,
`context_tokens`, `cost`, and `currency`. Values are non-negative numbers or `n/a`; unknown and
missing are never zero. A local or API-equivalent cost is not canonical cost and must be labeled as
non-comparable source data. Session/account data is never allocated, divided, or delta-inferred
into a role.

## Correlation and comparison

Role-scoped sidecar observations join only on an exact `run_id`. A native provider id without an
explicit mapping stays unjoined. A reviewed launch attribute or post-hoc one-to-one mapping is
acceptable; timestamp proximity is not exact correlation. Compare only the same metric, unit,
scope, collector semantics, and pricing basis. Subscription cost, API cost, and API-equivalent
estimates are separate bases.

## Coverage and dependency boundary

Retro computes `measured/eligible` plus a percentage per metric and comparable cohort. No eligible
measurements is `0/N (0%)`, never `0/0`. Zero or partial telemetry still supports duration, attempts,
rework, incomplete runs, verification outcomes, and task time to completion. Partial exact coverage may
list labeled observations but cannot produce totals, shares, rankings, or tier recommendations.
Totals/rankings require 100% comparable coverage; tier/effort recommendations also require at least
three completed like-for-like runs. The universal ledger never depends on a collector; no hook,
daemon, plugin, provider API, or sidecar is required for a task to close.

## Legacy compatibility

An eight-column header beginning `Point | Role | Tier | Model | Effort | Tokens in | Tokens out |
Session` is legacy and remains readable. Adoption appends the v2 marker/table below it and writes
only v2 events. Legacy rows without exact run ids remain legacy-scoped. Rollback removes only the
new v2 section and preserves legacy bytes. Migration and compatibility reads are fixture-tested.

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
