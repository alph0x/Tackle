# OpenAI Responses capability profile

Evidence snapshot: `docs/plans/tackle-usage-observability-v2/reference-docs/openai-responses.md` (captured 2026-09-04).

## Native scope

An integration that owns a Responses API request receives an exact response-level `usage` object,
stable response id, input/output totals, cached-input detail, cache-write detail where supported,
and reasoning-token detail.

## Exact correlation

The owning integration can carry a Tackle `run_id` in application metadata or map it to the stable
response id. Organization usage and account/project limit deltas remain account or project scope.

## Authority

The API response usage is authoritative for the request fields it exposes. API-equivalent prices,
subscription cost, and capacity deltas are not canonical run cost or token consumption.

## Privacy

Metadata and response payloads can contain user content. Persist only identifiers, measured metrics,
and provenance required for the sidecar; never copy prompts or full responses.

## Version sensitivity

Usage detail varies by model and API version. Record the response schema/version and set unsupported
cache or reasoning fields to `n/a` rather than assuming parity.

## Agent access

Exact fields are available only when the agent or optional integration controls the API request and
exposes the response. Codex Desktop task exports remain unknown unless a documented host surface appears.
