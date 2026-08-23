# Portable usage contract — `tackle-usage/1`

A versioned, harness-agnostic telemetry format that any agent harness can emit to record what a Tackle run actually consumed. It is an **additional ingest source** for the `usage.md` ledger — never a replacement, never a gating signal. Harnesses emit it; Tackle validates it (`tackle-check usage`), documents its correlation into the ledger, and mines its contract-only fields at retro.

## Schema

Versioned contract identifier: `tackle-usage/1`. A contract document is one JSON object, one per line, in `docs/plans/<slug>/usage-events.jsonl` (or any single file/stream passed to the validator). Unknown top-level fields are ignored — forward/backward compatible ingest.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schema` | string | yes | `tackle-usage/1` — the contract version |
| `session` | string | yes | Opaque session identifier; no format required |
| `initiative` | string | no | Initiative slug (`docs/plans/<slug>`) |
| `point` | string | no | Point id (`PLAN`, `RETRO`, `P-xx`) |
| `mode` | string | no | Run mode (`plan`/`execute`/`retro`/…) |
| `phase` | string | no | Phase name |
| `model` | string | no | Concrete model the harness ran |
| `tier` | string | no | Bound tier |
| `effort` | string | no | Effort level actually used |
| `tokens` | object | yes | Token block: `input`, `output`, `cache_read`, `cache_write` (each integer or `n/a`) |
| `requests` | integer/`n/a` | no | API requests |
| `tool_calls` | integer/`n/a` | no | Tool invocations |
| `compactions` | integer/`n/a` | no | Context-compaction events |
| `context` | integer/`n/a` | no | Context window in tokens |
| `duration_ms` | integer/`n/a` | no | Wall-clock duration |

Minimal valid document:

```json
{"schema":"tackle-usage/1","session":"s2026-08-22-1","tokens":{"input":"n/a","output":"n/a","cache_read":"n/a","cache_write":"n/a"}}
```

## Honesty

A field the harness does not expose is `n/a` — **never zero-as-truth, never estimated**. Zero is a measured value (`0` requests is a fact); a missing measurement is `n/a`. Inventing a number, or zero-filling a field the harness did not report, violates the contract. Unknown fields are ignored; `session` is opaque (no required format); a document is valid with or without any optional field.

## Correlation

The contract is an **additional ingest source** for the `usage.md` ledger: append/correlate safely, never fabricate, never silently replace an existing row. Mapping into ledger columns happens only where a column exists (`tokens.input` → Tokens in, `tokens.output` → Tokens out, `model` → Model, `tier` → Tier, `effort` → Effort, `point` → Point). Fields with no ledger column (`cache_read`, `cache_write`, `requests`, `tool_calls`, `compactions`, `context`, `duration_ms`) are mined by the retro recipes from `usage-events.jsonl`, never force-fitted into the 8-column schema. Recording stays informative, never gating: a missing value is `n/a`, not a missing row.

## Measurement layers

The contract sits in a three-layer measurement model:

- **Universal** — anything measurable without harness cooperation: files, lines, words, commands, timestamps. Always available; recorded by the executor directly.
- **Cooperative** — harness events this contract describes: tokens (incl. cache splits), requests, tool calls, compactions, context, duration. Available only when the harness exposes them; exposed values are recorded verbatim, unexposed ones are `n/a`.
- **Specific** — per-harness adapters turning proprietary counters into this contract. Out of scope for Tackle itself; a harness that wants to emit the contract writes its own adapter.

Tackle never installs hooks, never probes live telemetry, and never estimates a value the harness does not expose.
