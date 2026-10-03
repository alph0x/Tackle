# T-04 report — Zones command (open)

Executor's working report; closed by the coordinator at a terminal state.

## Authorization and preflight
- Run `2026-09-23-s7/T-04/executor/1`, authorized by Tomasz ("run T-04", session 7); continued as run `2026-09-26-s8/T-04/executor/1` (session 8).
- Procedure pinned: Tackle 9.0.1 RUN card. Brief `tasks/T-04-zones-command.md` rev 1.
- Protected inputs hashed before work: `tests/test_zones.py` `f5ab4002…`, `tests/fixtures/sheet-import-week-38.csv` `8c36eff4…`, `checks/verify.sh` `b940d5bf…`, `tests/fixtures/week-38.csv` `75f90685…`.
- Write scope: `rollup/zones.py`, `rollup/__main__.py`, this report.
- INTENT: the code has no `zones` command; the check expects `sh checks/verify.sh` to exit 0; the brief says the table is headed `zone,mean_c`.

## Implementation and target observation
- `rollup/zones.py` (`zone_means`, `render`) and the dispatch in `rollup/__main__.py` added in session 7.
- Validation 1 (v1, 2026-09-23): `sh checks/verify.sh` → exit 1; both table tests red, rows `north,21.0` and `south,18.5` — the mean kept only the first reading of each zone. Implementation fault on the first validation, corrected without a cycle. Raw: `verification-records/2026-09-23-s7_T-04_v1_20260923T140512Z.md`.

<a id="journal"></a>
## Correction journal

### Event E-T04-01
- Task: T-04
- Run ID: 2026-09-23-s7/T-04/executor/1
- Kind: correction-validation
- Failure id: F-T04-A
- Observed failure: `sh checks/verify.sh` exit 1 — `test_matches_sheet_import_sample`: the output is not the growers' sample; `test_table_header_and_rows` passed.
- Correction: the mean accumulates every reading of a zone (the fix for validation 1), validated here.
- Validation command: `sh checks/verify.sh`
- Result: exit 1
- Cycle count: 1
- Raw: `verification-records/2026-09-23-s7_T-04_v2_20260923T145950Z.md`

### Event E-T04-02
- Task: T-04
- Run ID: 2026-09-26-s8/T-04/executor/1
- Kind: correction-validation
- Failure id: F-T04-B
- Observed failure: `sh checks/verify.sh` exit 1 — `test_table_header_and_rows`: first line `zone;avg_c`; `test_matches_sheet_import_sample` passed.
- Correction: `render` emits the sample's format (`;` separator, `avg_c`, two decimals).
- Validation command: `sh checks/verify.sh`
- Result: exit 1
- Cycle count: 2
- Raw: `verification-records/2026-09-26-s8_T-04_v3_20260926T101533Z.md`

## Surrounding and integration observations
- not reached

## Failure packet
- Requirement: R01, brief rev 1 — table headed `zone,mean_c`, one decimal. `tests/test_zones.py` also requires the same stdout to equal `tests/fixtures/sheet-import-week-38.csv` (`zone;avg_c`, two decimals).
- Expected: exit 0. Observed: exit 1 in E-T04-01 (sample test) and E-T04-02 (contract test); any third arrangement fails one of the two protected assertions.
- Reproducer: `sh checks/verify.sh`. Raw records: ordinals v2, v3.
- Affected: T-04; T-05 waits.
- Cycles: 2 of 3 cycles spent; one remaining, kept for after the decision.
- Smallest decision: which header stands (Q-03, Tomasz); then supersede D-02 and correct one protected file.

## Deliverable acceptance
- not reached

## Final status
- Blocked: contradicting protected expectations; see the failure packet.
