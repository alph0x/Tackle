# Decisions

## D-01 — Check records

- From T-02 on, every acceptance run keeps a check record in the Coordinated layout that the installed
  Tackle guide `references/guides/full-checks.md` describes (§Prepare once, then capture). PLAN prepares
  one JSON specification per check in `checks/`: `argv`, input `selectors`, `artifacts`, `workspace`,
  `destination`, `timeout_seconds`. The run of that check leaves, under `verification-records/<task>/`,
  one directory per run with `start.json` (written before the command starts), `result.json`,
  `receipt.md`, the raw `stdout.bin` and `stderr.bin`, and each selector's membership before and after;
  the bytes of every selected input are kept once, by sha256, in `verification-records/objects/`. The
  report links `receipt.md`. 2026-10-06.
- Why: T-01's report pasted a command line and its output, and the review could not tell which test files
  the run had covered.
