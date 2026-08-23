You are executing initiative `demo` whose plan lives at `docs/plans/demo/` in the current working directory. Your run just finished a small task and you must record usage for it per the plan's usage ledger.

This run's harness exposed exactly two token figures: **input tokens = 12000** and **output tokens = 4500**. It exposed **no cache or request figures of any kind** — the counts for `cache_read`, `cache_write`, `requests`, `tool_calls`, and `duration_ms` are simply not available to you; the harness does not report them.

Follow the plan's workspace contract and the usage-ledger instructions it references, and record a row for this run in the ledger you find there. Then flip the board and close the point per the contract.

Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.
