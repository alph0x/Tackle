# History archive — Manifest summary

Entries moved verbatim out of `history.md` under house rule 6 (AGENTS.md), oldest first. Nothing here is
edited after the move; headings, references and failed attempts stay as they were written.

Moves: 2026-09-19 (session 5) — sessions 1–4, 78 lines.

---

## 2026-09-08 · session 1 · plan kickoff

### Intake (context gathered)
- Requirement: Imogen Hartley (depot operations lead): "the shift leads should see how many parcels an export has without opening it; the nightly digest should carry the number."
- Docs read: `README.md` of depot-tools; the scanner vendor's export note (header `scan_id,barcode,weight_kg,bay`, one parcel per row, returns carry an empty weight, exports are written once per shift under `exports/<date>-<shift>.csv`).
- Scope hints: counts for the digest; the CSV format is owned by the vendor and does not change; the digest template is owned by ops and rendered by a cron job the depot does not control.
- Codebase: `~/src/depot-tools`, a plain Python 3.10 package with `unittest`; no packaging, no CI, no linter. Git on `main`, three contributors over two years, last commit in June.
- Harness observed: Claude Code in the terminal; the host exposes no model list and no token telemetry, so the model map records `unknown` for `fast` and `frontier` and the session's own model for `standard`.

### Did
- Sizing: four tasks over several sessions with an owner review in the middle, so a Coordinated workspace at `docs/plans/manifest-summary/` rather than a one-file fix.
- Imogen asked for `docs/plans/` to be gitignored; D-01 recorded and `.gitignore` updated in the same session.
- Scaffolded the core files from the method's templates, filled the context line, file map, harness map and model map in `AGENTS.md`; `tasks/` empty for now.
- Drafted the objective (R01 count line, R02 digest) and the exclusions: no weights, no per-bay view, no change to the export format.
- Walked the repository with Imogen: `manifest/` is an empty package with a `README` stub; the digest lives outside this repo and will be snapshotted for T-04.

### Decisions
- D-01: `docs/plans/` gitignored.

### Blockers / open questions
- Q-01: should the line also carry total weight? Imogen to answer; the shape of T-03 and T-04 depends on it.

### Next
- Resolve Q-01, write the four briefs, run readiness.

## 2026-09-10 · session 2 · readiness

### Did
- Q-01 resolved with Imogen: counts only, because returns carry no weight and a total would mislead; D-02 recorded and Q-01 marked resolved.
- Four briefs compiled from the plan: T-01 reader (`read_rows`), T-02 fixture set and protected test, T-03 subcommand, T-04 digest line. Each brief names its inputs, its write scope and one acceptance command; T-04 stays Draft until the digest template is snapshotted.
- Readiness: citations re-checked against `manifest/` (then only an empty package, so T-01 cites the vendor note instead), the dependency chain T-01 → T-02 → T-03 → T-04 written into `plan.md` §5, T-01 set Ready to run (`ready: tasks/T-01-parse-rows.md rev 1`).
- Lint over the workspace: 16 of 16 rows pass; no placeholder left outside fenced blocks, every brief heading matches its board row, every Effort token is one of the four values.
- Resource ledger created with the v2 header; no rows yet because no run has started.

### Decisions
- D-02: counts only.

### Blockers / open questions
- none.

### Next
- Run T-01 when Imogen says go.

## 2026-09-15 · session 3 · T-01

### Did
- Imogen: "run T-01". Claimed as `2026-09-15-s3/T-01/executor/1`; start row appended; the board hash recorded before the claim and re-read after.
- `tests/test_rows.py` written first (two tests: every row read in order, weight converted to float), then `manifest/rows.py` with the `Parcel` record and `read_rows`.
- Validation 1: `python3 -m unittest tests.test_rows -q` → exit 0, two tests. Raw `verification-records/2026-09-15-s3_T-01_v1_20260915T113512Z.md`.
- `reports/T-01-report.md` written with the INTENT line, the observation and the receipt; board T-01 Complete; finish row appended (success, zero attempts, observed: the first validation passed).
- T-02 set Ready to run (`ready: tasks/T-02-fixture-set.md rev 1`); its inputs are Imogen's run-04 export and the wording review she scheduled for the 17th.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- T-02: fixture from the run-04 export; contract test and acceptance script from the wording review.

## 2026-09-17 · session 4 · T-02

### Did
- Imogen: "run T-02". Claimed as `2026-09-17-s4/T-02/executor/1`; start row appended.
- Wording review with Imogen and two shift leads (Dev and Marisol): the line reads `Parcels: <n>`; one line only; the digest quotes it verbatim; no trailing punctuation.
- `tests/fixtures/run-04.csv` added (three parcels from the 4 September morning run, weights as scanned); `tests/test_summary.py` written from the review (stdout is exactly `Parcels: 3` plus newline; a missing subcommand exits 2 with usage on stderr); `checks/acceptance.sh` drafted from the review notes so that T-03 has a single command to run: unit tests first, then the summary-line contract.
- Validation 1: `python3 -m unittest tests.test_rows -q && sh -n checks/acceptance.sh` → exit 0. Raw `verification-records/2026-09-17-s4_T-02_v1_20260917T150241Z.md`.
- Imogen signed off the three files in the session; `reports/T-02-report.md` drafted with her review note; closure deferred to the next session so that the decision protecting the files is recorded first and the board update happens in one place.

### Decisions
- none recorded yet; the protection of the three files goes to session 5 (became D-03).

### Blockers / open questions
- none.

### Next
- Close T-02, record D-03, set T-03 Ready.
