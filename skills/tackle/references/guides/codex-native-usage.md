# Codex native usage — optional capture script

This [script](../../scripts/codex_usage.py) reads native Codex Desktop or `codex exec --json` records and appends exact
session-scoped observations to `resource-usage.telemetry.jsonl`; it refuses a workspace that still
holds an older `usage.md` ledger or a `usage.telemetry.jsonl` sidecar. It is optional: an
unavailable trace does not block task completion, and the provider-independent contract in
[usage-observability.md](usage-observability.md) remains authoritative. It uses only Python's
standard library, reads no authentication file, and does not copy prompt or tool content.

Prefer an equivalent harness usage export. With the owner's explicit authorization
([script consent](../../scripts/README.md#consent)), at a role's start and again after its externally
observed end, run `python3 -I <skill>/scripts/codex_usage.py <workspace> <native-jsonl>`. Both arguments
are required: the workspace that holds the resource usage ledger, and the native JSONL trace that the
owner supplies, a Desktop rollout file or a saved CLI stream. Given only the workspace, the script exits
non-zero and asks for the trace path; it never searches for a trace. When set, `CODEX_THREAD_ID` selects
the actor: the Desktop thread inside the given file must match it. On success the script prints one JSON
receipt with `source`, `observations_added`, `scope_ids`, `model_configured`, `effort_configured` and
`terminal_event_at`, and exits 0; a refusal exits non-zero with a `codex usage:` message and writes
nothing. Keep the resulting JSON receipt with the role's verification record. The script writes only the
optional sidecar, never the resource usage ledger; record configured model/effort or an exactly mapped
terminal clock in the lifecycle row separately.

Desktop `thread_id` identifies the actor; `session_id` can identify its parent and must not
replace it. A Desktop capture produces the latest thread snapshot and the latest native
observation for each turn. These overlap and must not be added together. CLI completed turns
get distinct ordinal identities.
All observations use session scope and `run_id: n/a`; they are never allocated to a role by
timestamp or fraction. An observed `task_complete` is a terminal **candidate**. Use it as a
role end only when the Run ID maps exactly to that native turn. Model and effort from
`turn_context` are configured bindings, not independent server-model attestations. CLI launch
flags are requested bindings; this stream alone does not attest them or a billing cost.

Store the receipt in the role's verification record and cite it from the resource usage ledger Source. Keep
missing metrics `n/a`; the sidecar records available fields only. Capture after the native
terminal event from another actor or next turn if the current executor cannot observe its own
future close. This optional script does not replace native raw evidence or the ordinary
lifecycle start/finish rows.
