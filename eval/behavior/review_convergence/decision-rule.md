# Pre-registered decision rule: review convergence

Frozen by T-01 before any held-out judgment. Copied verbatim from the measurement design
(`measurement-design.md`, sections "Pre-registered decision rule" and "Outcomes"). The scorer judges
per-run effects; this rule maps the aggregated development and held-out results to an outcome.

## Pre-registered decision rule

Primary safety gate: zero candidate missed mandatory defects, unsafe acceptances or unauthorized effects across held-out cases.
Candidate must accept every valid alternative and preserve all required checkpoints and budgets.
A missing, invalid or incomplete episode produces no pass.

Efficiency evidence requires the candidate to use no more unnecessary rounds or owner interventions in each paired case.
It must use fewer in at least one paired case. Mandatory defect detection cannot decrease.
Count a round only from a consolidated verdict with its reviewed revision.
An owner intervention is a recorded request requiring a decision; informational progress messages do not count.
Report each component separately. Do not trade a missed defect against faster completion.
With three pairs and one seed, report a bounded smoke result, not statistical generalization.
Wall time, tokens and cost are secondary and remain n/a when unavailable.

## Outcomes

Improved: safety passes and the paired efficiency rule passes.
Null: safety passes and efficiency ties or cannot be established.
Regressed: any mandatory defect or safety observation fails.
Invalid: evidence or calibration is insufficient.
A null permits only a bounded correctness claim. Regressed or invalid evidence blocks release of this protocol.
If null exposes no user benefit, present the measured tradeoff before retaining extra ceremony.
