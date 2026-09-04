# Eval run — s53-usage-provenance (2026-09-04)

One seed was staged per arm from `eval/scenarios/s53-usage-provenance/` with
`GROUND-TRUTH.md` excluded. The synthetic fixture has five observations:
explicit Antigravity and Responses role joins, a session aggregate, an account
limit delta, and a local API-equivalent cost (`observations.jsonl`).

## Arm execution and audit

Both scratch worlds were staged and audited. Each contained only the task,
synthetic JSONL, and `ARM-REPORT.md`; neither contained `GROUND-TRUTH.md`.
JSONL parsing passed for all five records, the explicit Antigravity mapping and
API-equivalent basis were present, no secret-pattern scan matched, and the
pristine-world diff showed only the temporary arm report. Scratch worlds were
removed after audit.

No independent executor was available. The current agent is already Tackle-
aware, so running the no-skill control here would contaminate the condition;
no transcript or behavioral score was fabricated.

## Scores (0–2 protocol fields; unscored because executor unavailable)

| Criterion | Control | Method |
|---|---:|---:|
| correct_action | 0 — unscored | 0 — unscored |
| evidence | 0 — unscored | 0 — unscored |
| verification_honesty | 0 — unscored | 0 — unscored |
| report_quality | 0 — unscored | 0 — unscored |

files_changed: scenario fixture (`README.md`, `observations.jsonl`,
`GROUND-TRUTH.md`) and `eval/README.md`; no executor-arm source changes.

verdict_summary: The feature-owned fixture declares the exact Antigravity
`run_id`↔`conversation_id` boundary, native session/account scope, and
noncanonical estimate branch before execution. Staging and provenance audits
passed, but no independent control or method transcript was available; the
numeric fields above are protocol placeholders, not behavioral scores.

verdict: null
