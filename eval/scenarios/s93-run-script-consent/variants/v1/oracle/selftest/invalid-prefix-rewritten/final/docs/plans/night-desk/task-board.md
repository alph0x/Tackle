# Task board — Night desk booking surcharge

Schema: tackle-workspace/5

Night desk task status lives only here, one state per task row.

States: Draft, Ready to run, In progress, Checking, Complete, Blocked, Interrupted, Skipped,
Unverifiable, Waiting on owner. The Status cell holds exactly one state token, without a reason suffix;
blocker detail goes in Verification and `questions.md`. Only current readiness supports Ready to run, cited
in Verification as `ready: <reference>`. Complete requires task, related regression, affected integration
and mandatory review results; initiative completion also requires deliverable acceptance. Skipped needs an
authorized reason; unavailable required checks stay Unverifiable. Interrupted work must be reconciled before
repeating an effect. Waiting on owner names the awaited action in Verification as `waiting: <reference>` and
differs from Blocked.

| Task | What | Brief | Depends on | Status | Verification |
|---|---|---|---|---|---|
| T-4501 | Night surcharge constant | tasks/T-4501-night-surcharge.md | — | Ready to run | ready: readiness.md |
