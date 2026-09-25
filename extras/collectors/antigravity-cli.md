# Antigravity CLI capability profile

Evidence snapshot: `docs/plans/tackle-usage-observability-v2/reference-docs/antigravity-cli.md` (captured 2026-09-04).

## Native scope

Headless `agy -p --output-format json` returns one terminal conversation envelope with status,
duration, turns, and usage. `stream-json` adds init, step, tool, subagent, and terminal result
events; continued streams may carry cumulative counters.

## Exact correlation

A controlled optional integration creates one Tackle `run_id`, launches one headless role run, and
persists the returned `conversation_id` as an explicit one-to-one mapping. Interactive or continued
sessions without that mapping remain session-scoped and unjoined; a conversation id alone is not a
Tackle run id.

## Authority

Documented fields map `input_tokens`, `output_tokens`, `thinking_tokens`→`reasoning_tokens`,
`cache_read_tokens`, duration, terminal status, and observed tool-step counts. Native status is kept
in provenance. Cache-write tokens, request count, compactions, context tokens, and canonical cost
are `n/a` unless a newer documented surface exposes them.

## Privacy

Streams may include tool parameters, outputs, child-log locations, and interaction content. Collect
minimum metadata and never copy raw content into usage telemetry.

## Version sensitivity

Verify the installed CLI version: structured cache-read accounting was added during the 1.1 series,
and fields may be absent on older versions. Preserve unknowns as `n/a`.

## Agent access

The agent can consume JSON or stream events only when the user or an optional integration exposes the
headless command output. The profile documents capability; it does not install or activate `agy`.
