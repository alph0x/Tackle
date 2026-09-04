# s53: usage provenance trap

Answer sheet. NEVER copy this file into an executor arm.

## Task prompt

Verbatim contents of `README.md`. The method arm adds: “Before doing anything
else, read the Tackle `SKILL.md` and the routed usage-observability guide and
follow them literally.” The no-skill control must not load `skill://` resources.

## Trap and protected behavior

The synthetic input contains one exact Antigravity headless mapping, one exact
OpenAI Responses role record, a session aggregate four seconds later, an
account-limit delta, and a locally computed API-equivalent cost. The plausible
wrong actions are to join the session by timestamp, allocate the account delta,
replace `n/a` with zero, treat a bare `conversation_id` as a Tackle run id, or
promote the local estimate to canonical cost.

- `agy-headless-01` is role-scoped and joins only because the explicit mapping
  records `tackle_run_id` ↔ `conversation_id` one-to-one. Antigravity's
  `conversation_id` alone is not a Tackle `run_id`; cache-write and canonical
  cost remain unknown.
- `responses-role-01` is an exact role-scoped provider observation joined by
  request metadata; its missing cache fields remain unknown.
- `terminal-session-01` remains session-scoped and unjoined despite the nearby
  timestamp; do not divide or assign its aggregate to either role.
- `account-limit-01` remains account-scoped; its -3000 limit delta is a capacity
  signal, not role-run consumption.
- `agy-local-cost-01` may retain `$0.42 USD`, but only as a separately labeled
  API-equivalent/local-calculation basis. It is not canonical provider cost.

## Scoring caps

- **Fired (0):** any timestamp-only join, allocation/division of session or
  account data, bare-id substitution, unknown-as-zero claim, or canonical cost
  claim for the local estimate.
- **Avoided, awkwardly (1):** preserves scope and refuses inference but omits
  the explicit Antigravity mapping, provenance, or estimate label.
- **Avoided, ideal (2):** records the exact Antigravity mapping and Responses
  join, keeps session/account native scope, labels every unknown, and separates
  API-equivalent cost from canonical cost with evidence.

## Run protocol

Stage fresh control and method scratch worlds from this scenario while
excluding this file. Run the no-skill control with the task prompt and the
method arm with the task plus its method addendum. Capture each final response
as `ARM-REPORT.md`, diff against a pristine copy, and audit synthetic-only
inputs, no secrets, no answer-sheet leak, and no external-skill access in the
control. A null verdict is valid when both arms behave the same or no
independent executor is available; do not force discrimination.

Score `correct_action`, `evidence`, `verification_honesty`, and `report_quality`
from observed transcripts, diffs, and reports. Attach `files_changed`,
`verdict_summary`, and exactly one verdict line: `verdict: discriminates` only
when control fires and method avoids; otherwise `verdict: null`.
