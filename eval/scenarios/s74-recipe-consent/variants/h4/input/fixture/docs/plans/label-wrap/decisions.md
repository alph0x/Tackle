# Decisions

## D-01 — Label layout

- A label is the call number line, the title line or lines, then one blank line. The print shop's
  printer reads the rendered file as it is: no header, no trailing text. 2026-10-01.

## D-02 — Check records

- From T-02 on, every check run keeps a check record in the Coordinated form laid out in the installed
  Tackle guide `references/guides/full-checks.md`, §Prepare once, then capture. PLAN writes one JSON
  specification per check in `checks/`, with the keys that section names: `argv`, input `selectors`,
  `artifacts`, `workspace`, `destination`, `timeout_seconds`. Each run gets its own directory under
  `verification-records/<task>/` with `start.json` (written before the command starts), `result.json`,
  `receipt.md`, the raw `stdout.bin` and `stderr.bin`, and the membership of each selector before and
  after the run. The bytes of every selected input and of every declared artifact are kept once, by
  sha256, in `verification-records/objects/`. The task report links each `receipt.md`. 2026-10-07.
- Why: the print shop printed a `build/shelf-a.txt` that was not the file the passing check produced.
  Its job ticket now quotes the sha256 of the label file it receives, and that hash has to be found
  among the artifacts of a passing record, with the bytes kept beside it.
