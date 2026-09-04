# Cursor CLI capability profile

Evidence snapshot: `docs/plans/tackle-usage-observability-v2/reference-docs/cursor.md` (captured 2026-09-04).

## Native scope

CLI observations are chat/session-scoped; Admin API observations are team/account-scoped. Keep
these scopes separate. CLI token and cost fields are `n/a` unless a newer documented output
exposes them; Admin API values are not automatically one role run.

## Exact correlation

Cursor `session_id` and `request_id` are native identifiers, not Tackle `run_id`s. A controlled
integration may carry an explicit Tackle id or reviewed one-to-one mapping; otherwise preserve
session or team scope and remain unjoined. Nearby timestamps do not prove a role join.

## Authority

The CLI JSON envelope is authoritative for observed duration, status/result, session id, and
optional request id. Admin API usage/cost is authoritative only within team scope; canonical role
cost and role token totals remain `n/a` without exact attribution. Local estimates are separate.

## Privacy

CLI stream events may include prompts, assistant text, files, and tool arguments/results. Admin API
access uses a privileged team key. Collect minimum identifiers and metrics; never persist raw
conversations, tool payloads, or credentials in telemetry.

## Version sensitivity

Cursor CLI is documented as beta and its flags, output schema, sessions, and Admin API may change.
Verify installed CLI/API versions and set missing token, cost, or correlation fields to `n/a`.

## Agent access

An agent can consume CLI fields only when print output is exposed; Admin API data requires an
authorized team-admin integration. This profile does not install, activate, or assume access.
