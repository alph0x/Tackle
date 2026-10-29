# Task board — Price rule for bakery orders

Schema: tackle-workspace/5

Task status lives only here, one state per row.

States: Draft, Ready to run, In progress, Checking, Complete, Blocked, Interrupted, Skipped, Unverifiable, Waiting on owner. The Status cell holds exactly one state token, without a reason suffix; blocker detail goes in Verification and `questions.md`. Only current readiness supports Ready to run, cited in Verification as `ready: <reference>`. Complete requires task, related regression, affected integration and mandatory review results; initiative completion also requires deliverable acceptance. Skipped needs an authorized reason; unavailable required checks stay Unverifiable. Interrupted work must be reconciled before repeating an effect. Waiting on owner names the awaited action in Verification as `waiting: <reference>` and differs from Blocked.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-4201 | Price rule for bakery orders | tasks/T-4201-order-total.md | — | Checking | reviews/T-4201-review-01.md; ready: readiness.md |
