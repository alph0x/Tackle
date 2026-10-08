# Decisions

## D-01 — Check records

- Every acceptance run keeps a check record under `verification-records/<task>/`, one directory per run,
  in the layout of T-01's record: `start.json` written before the command starts, `result.json` after
  it, `receipt.md`, the raw `stdout.bin` and `stderr.bin`, and the bytes of every input the run read,
  kept in `blobs/` under their sha256. The report links `receipt.md`. 2026-10-01.

## D-02 — Carried records

- A task that changes a file covered by an earlier accepted record carries that record into its own, so
  the earlier acceptance can still be reconstructed after the change. Before its acceptance run it
  re-checks the earlier record: the stream and `blobs/` files against the digests in its `result.json`,
  child exit 0 and `accepted: true`. Its own `result.json` then lists the earlier record under
  `prior_records` (path → sha256 of that `result.json`) and keeps the earlier record's blobs among its
  own (`prior_objects`), as `references/guides/record-lifecycle.md` describes. 2026-10-03.
