# Kimi Code capability profile

Evidence snapshot: `docs/plans/tackle-usage-observability-v2/reference-docs/kimi-code.md` (captured 2026-09-04).

## Native scope

Kimi records are persistent sessions and local exports. Context percentages are context
observations, not cumulative role-run usage. Token totals, cost, and role scope are `n/a` unless
a newer documented export explicitly exposes them.

## Exact correlation

Kimi session IDs identify Kimi sessions, not Tackle role runs. Require an explicit Tackle `run_id`
or reviewed one-to-one mapping from a controlled integration; resume behavior and timestamps do
not create correlation. Otherwise keep the session unjoined.

## Authority

Transcript, stream, and export fields are authoritative only for fields they visibly expose. This
profile makes no canonical token or billing claim: unsupported tokens, cost, requests, and hidden
metrics remain `n/a`; subscription limits are not role cost.

## Privacy

Exports can contain conversation content, tool activity, project files, and a global log with
events from other sessions. Prefer `--no-include-global-log`, collect minimum metadata, and never
copy prompts, outputs, or credentials into telemetry.

## Version sensitivity

The current Node.js CLI replaced the legacy Python/uv CLI; flags, session storage, stream fields,
and export contents may change. Verify the installed version and degrade undocumented fields to
`n/a`; do not mix legacy and current formats silently.

## Agent access

An agent can consume values only when the harness exposes CLI transcript, stream JSON, or an
explicitly permitted session export. The profile does not install, activate, or assume access.
