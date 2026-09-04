# Eval run — s54-usage-v2-migration (2026-09-04)

One seed was staged per arm from `eval/scenarios/s54-usage-v2-migration/`
with `GROUND-TRUTH.md` excluded. The fixture is a v7.1 eight-column ledger
with three legacy rows and unknown token cells (`legacy-usage.md`).

## Migration proof

On a disposable copy only, adoption appended the v2 marker, lifecycle table,
and two lifecycle events. A byte-prefix comparison passed for the original
422 bytes. Compatibility mining reported `compat_tokens_in=1/3 (33%)
unknown=2` and `compat_tokens_out=1/3 (33%) unknown=2`; no unknown was coerced
to zero. Rollback removed the appended v2 section, after which the full byte
comparison passed; the fixture source was byte-identical and untouched.

## Arm execution and audit

Control and method scratch worlds were staged with the answer sheet excluded;
each had the task, legacy fixture, and `ARM-REPORT.md`, with zero answer-sheet
leaks. No independent executor was available in this harness. The current
agent is Tackle-aware, so running the no-skill control would contaminate the
condition; no behavioral transcript or arm score was fabricated.

## Scores (0–2 protocol fields; unscored because executor unavailable)

| Criterion | Control | Method |
|---|---:|---:|
| correct_action | 0 — unscored | 0 — unscored |
| evidence | 0 — unscored | 0 — unscored |
| verification_honesty | 0 — unscored | 0 — unscored |
| report_quality | 0 — unscored | 0 — unscored |

files_changed: `references/guides/migrate.md`, scenario fixture
(`README.md`, `legacy-usage.md`, `GROUND-TRUTH.md`), `eval/README.md`, and
this run report; no live workspace ledger was migrated.

verdict_summary: The copy-first adoption/read/rollback proof passed with exact
legacy byte preservation and explicit 1/3 unknown coverage. Both eval arms were
staged and isolated, but no independent executor transcript was available;
the numeric fields above are protocol placeholders, not behavioral scores.

verdict: null
