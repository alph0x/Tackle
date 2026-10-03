<a id="task-t-02--feed-builder"></a>
# Task T-02 — Feed builder

> Self-contained: work from this file and its named inputs.

## Purpose and scope

- **Depends on**: T-01 — `read_catalog`.
- **Traces to**: R01, R02 (`plan.md` §2).
- **Write scope**: `sync/feed.py`, `sync/__main__.py`, `tests/test_feed.py`, `docs/plans/catalog-sync/reports/T-02-report.md`.
- **Autonomy**: L2
- **Effort**: low
- **Budget**: 3 correction cycles.
- **Procedure revision**: Tackle 9.0.1 RUN card.
- **Inputs**: the storefront's sample `tests/fixtures/expected-feed.json` (D-02); D-03.
- **Goal**: `build_feed(rows)` equals the sample for the fixture catalog; `python3 -m sync feed <catalog.csv> <feed.json>` writes it.
- **Non-goals**: no fields beyond the storefront's four; no change to the sample.

## Contract and cases

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| normal | the fixture catalog | feed equal to the sample | `tests/test_feed.py` |
| boundary | stock 0 | item kept | `tests/test_feed.py` |

## Acceptance and recovery <!-- SEALED: D-02 -->

```sh
python3 -m unittest tests.test_feed -q
```

- **Task check**: exit 0.
- **Recovery**: within the budget; then stop and report.
