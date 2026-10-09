# Decisions

## D-01 — Executors

- T-01 ran in a Codex CLI executor that the owner launched with `codex exec --json` outside the
  coordinating session; its stream is saved as `runs/T-01-executor.jsonl`. From T-02 on, tasks run in
  the coordinating session. 2026-10-05.

## D-02 — Exact usage from saved executor streams

- An executor cannot see its own end, so its ledger finish row leaves tokens and end time `n/a`. When
  its saved stream holds completed-turn usage, the next RUN session imports that usage into this
  workspace's `resource-usage.telemetry.jsonl`, in the format of the installed Tackle guide
  `references/guides/usage-observability.md` (§Optional sidecar): one observation per completed turn,
  session scope, `run_id` `n/a`, the turn's token counts as metrics, the stream path as source. The
  session keeps a receipt of the import (stream path, observations added, their scope ids) under
  `verification-records/<task>/` and cites it from that task's finish row Source. 2026-10-06.
- Why: the owner wants the executor's token cost next to the coordinating sessions before deciding
  whether to keep a separate executor for the next initiative.
