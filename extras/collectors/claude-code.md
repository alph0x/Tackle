# Claude Code capability profile

Evidence snapshot: `docs/plans/tackle-usage-observability-v2/reference-docs/claude-code.md` (captured 2026-09-04).

## Native scope

Interactive `/usage` is session-scoped. Opt-in OpenTelemetry can expose request spans with model,
duration, input/output/cache tokens, request identifiers, and attempt/success data. A status-line
context field is a current-context observation, not cumulative role usage.

## Exact correlation

An integration may add an explicit Tackle run attribute or apply a reviewed mapping from a native
session/request id. Native `session.id` alone does not prove a Tackle role; without the mapping,
retain session scope and do not join it.

## Authority

Provider- or harness-reported token and request fields are exact observations when the export is
available. `/usage` dollar figures and `total_cost_usd` are local estimates, not canonical billing.

## Privacy

OpenTelemetry is opt-in and may expose prompts, responses, tool details, or raw API bodies. Request
only the minimum fields needed for lifecycle analysis; never copy content into telemetry.

## Version sensitivity

CLI flags, status-line fields, and OTel attributes can change. Verify the installed Claude Code
version and degrade missing fields to `n/a`; do not treat context fields as cumulative totals.

## Local transcripts

Observed on Claude Code 2.1.293 (desktop app), 2026-10-08. Each session writes
`~/.claude/projects/<project>/<session>.jsonl`, and each subagent writes
`<session>/subagents/agent-<id>.jsonl` with a `.meta.json` that names its description and a model
alias. Each assistant event carries the full model name and a `usage` object with input,
cache-creation, cache-read and output tokens. One request can span several events with the same
`message.id`; the last one holds the final counts. Deduplicated by `message.id`, these are exact
per-request observations for the scope they describe. The [usage guide](../../skills/tackle/references/guides/usage-observability.md#claude-code-native-sources)
says how a coordinator turns them into sidecar records.

## Agent access

The agent can read the local transcripts above when its file tools reach the projects directory.
Otherwise it consumes these values only when the user or an optional integration exposes command
output, JSON, or an OTel stream. No workflow can assume either access without checking.
