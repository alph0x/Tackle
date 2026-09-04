# Usage observability — portable contract

This guide defines the provider-independent lifecycle ledger and the optional exact-telemetry
sidecar. It is a documentation contract, not a collector or executable.

## Lifecycle records

New workspaces declare `Schema: tackle-observability/2` in `usage.md` and use this exact table:

| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

`Run ID` is opaque and workspace-unique; the portable default is
`<YYYY-MM-DD-sN>/<point>/<role>/<ordinal>`. `Event` is `start`, `finish`, or
`observe-incomplete`. A role appends `start` before substantive work and `finish` at close. A
Coordinator may append `observe-incomplete` when a start lacks a finish, but that observation time
is not a claimed end and derived duration remains `n/a`.

Legal flow:

```text
absent -> start(running) -> finish(success|failed|blocked|aborted)
                         -> observe-incomplete(incomplete)
```

Exactly one start and at most one terminal event are valid. An orphan terminal, duplicate start,
duplicate terminal, negative count, or mismatched Point/Role is invalid. Missing values are `n/a`,
never zero and never estimated. Lifecycle recording is informative and never gates point closure.

## Optional sidecar

`usage.telemetry.jsonl` contains one JSON object per observation with schema
`tackle-observability-telemetry/1`. Required envelope fields are `schema`, `captured_at`,
`collector`, `source`, `scope`, `scope_id`, `run_id` when `scope=role`, `metrics`, and
`provenance`. Scope is `role`, `session`, or `account`; a session/account observation without exact
attribution uses `run_id: n/a`.

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
rework, incomplete runs, verification outcomes, and point time-to-green. Partial exact coverage may
list labeled observations but cannot produce totals, shares, rankings, or tier recommendations.
Totals/rankings require 100% comparable coverage; tier/effort recommendations also require at least
three completed like-for-like runs. The universal ledger never depends on a collector; no hook,
daemon, plugin, provider API, or sidecar is required for a point to close.

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
sidecar is valid and never a point-level failure.
