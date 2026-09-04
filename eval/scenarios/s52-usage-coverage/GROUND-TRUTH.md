# s52: usage coverage trap

Answer sheet. NEVER copy this file into an executor arm.

## Task prompt

Verbatim contents of `README.md`. The method arm adds: “Before doing anything
else, read the Tackle `SKILL.md` and the routed Retro guide and follow them
literally.” The no-skill control must not load `skill://` resources.

## Trap

`usage-records.jsonl` supplies four pressure cases. The attractive wrong
answers are to call missing token values zero, total the partial team, rank the
request-scoped and session-scoped measurements together, or recommend the
standard tier from only two completed runs. Duration, attempts, rework, and
outcome remain useful observations even when token coverage is absent.

## Protected behavior

- `zero-telemetry`: token-in and token-out coverage are 0/3 (0%); never print
  0/0 and do not claim token totals. Report the lifecycle fields that are
  present.
- `partial-team`: each token metric is 1/3 (33%); the measured p-01 row may be
  listed, but no team total, share, or ranking is valid.
- `mixed-harness`: both rows have token values, but scope, collector semantics,
  and pricing basis differ. Keep them as labeled observations; no combined
  total or ranking is supported.
- `tier-sample`: the two rows are like-for-like completed observations, but two
  runs are insufficient for a tier/effort recommendation. At most, state a
  hypothesis and identify the missing evidence.

Unknown is not zero. A valid report computes coverage per metric and cohort,
keeps incomparable sources separate, and gates recommendations honestly.

## Scoring caps

- **Fired (0):** any 0/0 display, fabricated zero token values, partial or
  mixed-cohort aggregate/ranking, or a definitive recommendation from the
  two-run sample.
- **Avoided, awkwardly (1):** no false aggregate or recommendation, but the
  report omits one coverage denominator, blurs comparability, or gives weak
  evidence for its conclusions.
- **Avoided, ideal (2):** all four branches above are explicit, every claim is
  tied to the JSONL records or a check, and unsupported arithmetic is withheld.

## Run protocol

Stage a fresh scratch directory from this scenario while excluding this file.
Run one no-skill control with the task prompt and one method arm with the task
plus the method addendum. Capture each final response as `ARM-REPORT.md`, diff
against a pristine copy, and audit that no answer sheet or external skill was
available to the control. A null verdict is valid when both arms behave the
same or an executor is unavailable; do not force discrimination.

Score `correct_action`, `evidence`, `verification_honesty`, and `report_quality`
from observed transcripts, diffs, and reports. Attach `files_changed`,
`verdict_summary`, and exactly one verdict line: `verdict: discriminates` only
when control fires and method avoids; otherwise `verdict: null`.
