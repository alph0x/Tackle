# OpenCode capability profile

Evidence snapshot: `docs/plans/tackle-usage-observability-v2/reference-docs/opencode.md` (captured 2026-09-04).

## Native scope

OpenCode's documented sessions, project-filtered stats, and exports are session/project or
aggregate observations, not automatically one Tackle role run. Token and cost fields are `n/a`
when their semantics are not exposed clearly.

## Exact correlation

OpenCode session IDs are not Tackle `run_id`s. Use an explicit Tackle run attribute or reviewed
one-to-one mapping from a controlled integration; timestamps and matching prompts are insufficient.
Without that mapping, preserve session/project scope and leave the observation unjoined.

## Authority

Use exported provider-reported fields only when their source is identified. The documented stats
cost display is not asserted as canonical billing; canonical role cost is `n/a` without an
authoritative basis. API-equivalent calculations remain separately labeled.

## Privacy

Session exports and JSON events can contain prompts, tool calls, outputs, paths, and project data.
Collect minimum identifiers and metrics; never copy raw transcripts into the telemetry sidecar.

## Version sensitivity

CLI flags, event fields, stats output, storage, and export shape are version-sensitive. Verify the
installed version and degrade undocumented token, cost, correlation, and context fields to `n/a`.

## Agent access

An agent can consume values only when the user or an optional integration exposes CLI output,
session export, or an allowed server API. This profile does not install or activate a collector.
