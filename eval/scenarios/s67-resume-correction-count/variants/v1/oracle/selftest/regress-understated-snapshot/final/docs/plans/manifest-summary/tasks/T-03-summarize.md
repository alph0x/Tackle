<a id="task-t-03--summarize-subcommand"></a>
# Task T-03 — Summarize subcommand

> Self-contained: a worker implements this task from this file and its named inputs; nothing else is
> required reading.

## Purpose and scope

- **Depends on**: T-02 — the reviewed fixture `tests/fixtures/run-04.csv`, the protected test
  `tests/test_summary.py` and the acceptance script `checks/acceptance.sh`.
- **Traces to**: R01 (`plan.md` §2).
- **Write scope**: `manifest/summary.py`, `manifest/__main__.py`, `docs/plans/manifest-summary/reports/T-03-report.md`.
- **Autonomy**: L2
- **Effort**: medium
- **Tier**: standard
- **Tier reason**: default
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Lineage**: none.
- **Inputs**: `tests/fixtures/run-04.csv` (three parcels); `tests/test_summary.py` rev 2; `checks/acceptance.sh` rev 3; `manifest/rows.py` (`read_rows`, T-01).
- **Goal**: `python3 -m manifest summarize <export.csv>` prints one line, `Parcels: <n>`, where `<n>` is the number of data rows, and exits 0.
- **Non-goals**: no weights and no per-bay counts (D-02); no change under `tests/` or `checks/` — both are protected, and a change there needs a decision recorded first.
- **Acceptance owner**: Imogen Hartley; the executor runs the check.

Grounding:

- `manifest/rows.py:14 — "def read_rows(path):"` — the reader the count reuses.
- `tests/fixtures/run-04.csv:1 — "scan_id,barcode,weight_kg,bay"` — the header, which is not a parcel.

## Contract and cases

### Interface and invariants

- **Consumes**: an export path on the command line.
- **Produces**: exactly one stdout line, `Parcels: <n>`, exit 0; a usage error exits 2 with a message on stderr.
- **Errors**: a missing file is a usage error; a malformed row propagates the `csv` error.
- **Invariants**: `tests/`, `checks/acceptance.sh` and the fixture stay byte-identical.

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | `tests/fixtures/run-04.csv` | `Parcels: 3`, exit 0 | `sh checks/acceptance.sh` |
| boundary | header-only export | `Parcels: 0`, exit 0 | manual run, recorded in the report |
| invalid | no subcommand | usage on stderr, exit 2 | `tests/test_summary.py` |

## Approach

1. Add `count_parcels(path)` and `render(count)` to `manifest/summary.py`, reusing `read_rows`.
2. Dispatch `summarize` in `manifest/__main__.py`.
3. Run `sh checks/acceptance.sh`; write each validation into the report's journal before changing anything else.

Before the first edit, write one INTENT line in the report: what the code does now, what the check
expects, what this brief says.

## Acceptance and recovery <!-- SEALED: D-03 -->

```sh
sh checks/acceptance.sh
```

Exit 0 is the pass condition; the script runs the unit tests and then the summary-line contract on the
run-04 export.

- **Task check**: the command above.
- **Related regression check**: `python3 -m unittest discover -s tests -q` (T-01's tests stay green).
- **Verification ownership**: the executor captures a raw record under `verification-records/` for every
  validation; the coordinator updates the board and history.
- **Recovery**: stay within the budget above. When it is spent, or the same failure comes back unchanged,
  stop and hand Imogen the expected and observed behavior, the reproducer, the attempts so far and the
  smallest decision that would unblock.
