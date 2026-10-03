<a id="task-t-04--zones-command"></a>
# Task T-04 — Zones command

> Self-contained: a worker implements this task from this file and its named inputs; nothing else is
> required reading.

## Purpose and scope

- **Depends on**: T-02 — `tests/fixtures/week-38.csv`, the growers' sample `tests/fixtures/sheet-import-week-38.csv`, the protected `tests/test_zones.py` and `checks/verify.sh`.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `rollup/zones.py`, `rollup/__main__.py`, `docs/plans/zone-rollup/reports/T-04-report.md`.
- **Autonomy**: L2
- **Effort**: medium
- **Tier**: standard
- **Tier reason**: default
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Lineage**: none.
- **Inputs**: `tests/fixtures/week-38.csv` (two zones, two readings each); `tests/fixtures/sheet-import-week-38.csv` rev 1; `tests/test_zones.py` rev 1; `checks/verify.sh` rev 2; `rollup/readings.py` (`read_readings`).
- **Goal**: `python3 -m rollup zones <readings.csv>` prints `zone,mean_c` and one `zone,<mean>` row per zone (one decimal), exit 0.
- **Non-goals**: no humidity, no min/max (D-03); no edit under `tests/` or `checks/` (protected by D-02).
- **Acceptance owner**: Tomasz Wierzbicki; the executor runs the check.

Grounding:

- `rollup/readings.py:13 — "def read_readings(path):"` — the reader the means are built from.
- `tests/fixtures/week-38.csv:1 — "zone,taken_at,temp_c"` — the export header.

## Contract and cases

### Interface and invariants

- **Consumes**: an export path on the command line.
- **Produces**: a CSV table on stdout, header `zone,mean_c`, rows in first-appearance order, exit 0; usage errors exit 2.
- **Errors**: a missing file is a usage error; a malformed row propagates the `csv` error.
- **Invariants**: `tests/`, `checks/verify.sh` and the fixtures stay byte-identical.

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | `tests/fixtures/week-38.csv` | `zone,mean_c` / `north,21.5` / `south,19.0` | `sh checks/verify.sh` |
| boundary | one reading in a zone | that reading as the mean | manual run, recorded |
| invalid | no subcommand | usage on stderr, exit 2 | `tests/test_zones.py` |

## Approach

1. `zone_means(path)` and `render(means)` in `rollup/zones.py`, built on `read_readings`.
2. Dispatch `zones` in `rollup/__main__.py`.
3. Run `sh checks/verify.sh`; each validation goes into the report's journal before the next change.

Write one INTENT line in the report before the first edit: what the code does now, what the check expects,
what this brief says.

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
sh checks/verify.sh
```

Exit 0 passes; the script runs the unit tests (the table contract and the sheet import sample) and a smoke run on week 38.

- **Task check**: the command above.
- **Related regression check**: `python3 -m unittest discover -s tests -q`.
- **Verification ownership**: the executor captures each validation under `verification-records/`; the coordinator updates board and history.
- **Recovery**: inside the budget above. Once it is spent, or the same failure returns unchanged, stop and give Tomasz the expected and observed behavior, the reproducer, the attempts so far and the smallest decision that unblocks.
