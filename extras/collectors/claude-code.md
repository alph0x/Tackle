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

## Agent access

The agent can consume these values only when the user or an optional integration exposes command
output, JSON, or an OTel stream. No Markdown-only workflow can assume automatic access.
