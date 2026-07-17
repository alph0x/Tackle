# Failure modes — symptom → Tackle rule

A short catalog of common execution failures, what each looks like from the outside, and the Tackle rule that prevents it. Use this as a checklist during `/tackle-verify`, audits, and point reviews.

| # | Failure mode | Symptom | Prevented by |
|---|---|---|---|
| 1 | **Unprompted fixing** | User asked "why?"; agent edited files | INTENT gate (point briefing) + intake classification (question shape changes nothing) |
| 2 | **Wrong-deliverable guess** | Agent built interpretation A; user meant B | Intake gate: ask one pointed question with a recommended interpretation |
| 3 | **Re-litigating settled decisions** | Agent reopens choices the user already made | Intake: extract decisions already made; never re-derive |
| 4 | **Fake "done"** | No one can say how the result was checked | Two-halves verification (point briefing acceptance), named per point |
| 5 | **Invented APIs / facts** | Code calls endpoints or cites figures that do not exist | Ground every claim in `file:line`; primary sources beat memory |
| 6 | **Sequential crawling** | One lookup at a time; long tasks take forever | Parallelize independent reads/lookups; use subagents for whole work units |
| 7 | **Context flooding** | Whole files and logs dumped into the conversation | Read narrow, never re-read; quote load-bearing lines only |
| 8 | **Analysis paralysis** | Research continues after it stopped changing the plan | Two batches of lookups, then a stated reason or stop |
| 9 | **Plowing through surprises** | Evidence contradicted the plan; agent forced the plan anyway | INTENT gate: state the contradiction and re-route the loop |
| 10 | **Scope creep** | Drive-by refactors, style rewrites, "improvements" nobody asked for | INTENT gate + smallest correct change |
| 11 | **Silent step-dropping** | Item 7 of 9 quietly never happened | Written checklist audited against the ask before reporting |
| 12 | **Retry thrash** | Same failing fix attempted with small variations, forever | 3-cycle retry bound (team.md Driver / AGENTS.md rule 5) |
| 13 | **Verification theater** | "This should work now" with nothing run; target passes but build breaks | Two-halves verification (point briefing acceptance) |
| 14 | **Spec betrayal** | Code changed to satisfy a check that contradicts the spec/README | INTENT-gate authority order: user > spec > tests > current code |
| 15 | **Compliance theater** | INTENT lines and evidence blocks written plausibly without running anything; maker and checker share the same model's blind spots | Partially mitigated: re-runnable-output evidence + reward-hacking guard + independent checker + checker≠maker tier (best-effort). **Residual risk accepted**: fabricated text is caught only by `/tackle-judge` re-running claims — no mechanical detection exists today |

## Reading an audit

A skipped rule creates the risk in its row. A **faked** rule is worse: the transcript claims the step happened but the observation is missing, which is the failure wearing the rule as a costume. The audit's job is to catch the costume.

The three failures that cost the most in practice are **unprompted fixing** (destroys trust), **retry thrash** (burns time), and **verification theater** (ships broken work labeled as done). If an audit can only check three things, check those.
