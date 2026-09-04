# Oh My Pi capability profile

Evidence snapshot: `docs/plans/tackle-usage-observability-v2/reference-docs/oh-my-pi.md` (captured 2026-09-04).

## Native scope

The public `@oh-my-pi/omp-stats` package parses session JSONL, aggregates to SQLite, and exposes
`omp stats --json` plus programmatic dashboard helpers. Native summaries are session, folder, and
model aggregates; they are not automatically one Tackle role run.

## Exact correlation

A controlled integration can map one exported session to a Tackle `run_id` through reviewed
metadata. Without that mapping, preserve the native session or aggregate scope and keep it
unjoined; private log filenames and timestamps are not exact correlation.

## Authority

Provider-reported usage on assistant messages and public stats fields are exact observations when
available. Subscription-backed dollar values are explicitly API-equivalent estimates and cannot
populate canonical `cost`.

## Privacy

Session JSONL may contain prompts, responses, tool data, and folder identifiers. Request aggregate
metrics only and do not copy private session content into the sidecar.

## Version sensitivity

The package and its JSONL schema are version-sensitive. Use current `omp stats --json` output;
older names such as `UsageStatistics` are not a stable public contract without history verification.

## Agent access

The agent can consume stats only when the installed harness permits the command, session logs, or
programmatic package API. Internal calculations are not assumed to be exposed.
