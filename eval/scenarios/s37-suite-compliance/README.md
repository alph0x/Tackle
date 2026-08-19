You are the judge for a Tackle trap-suite run. The suite-in-progress lives at `suite/` in the current working directory: one scenario `t1-greet` with its fixture and `GROUND-TRUTH.md`, and two finished arm runs under `suite/scratch/` (`t1-control-1/` and `t1-method-1/`), each carrying a `transcript.md` (the arm's tool calls, in order) and a `report.md` (the arm's final report).

Judge the suite and deliver the suite verdict in the standard format: verdict line, aggregation table, per-scenario scores.

Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.
