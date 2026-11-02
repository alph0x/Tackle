# Task T-4401 — Parcel report correction

> Self-contained: use the named inputs and this brief.

## Purpose and scope

- **Depends on**: none.
- **Write scope**: `pkg/`, `tests/`, `docs/plans/parcel-reports/reviews/`.
- **Autonomy**: L2
- **Effort**: low
- **Goal**: loading an empty input returns no rows and parcel reports continue to count rows correctly.
- **Non-goals**: keep the public helper name selected by the owner.

## Acceptance and recovery

The project checks below must succeed:

```sh
python3 -m unittest discover -s tests -p 'test*.py'
python3 tools/check_consumers.py
```

The correction diff and the preceding review are under `reviews/`.
