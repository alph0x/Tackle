# Task T-1001 — Slot parser

- **Write scope**: `lanes/slots.py`, `docs/plans/lane-bookings/reports/T-1001-report.md`
- **Depends on**: none.
- **Decisions**: D-1001.
- **Goal**: `parse_slot(text)` turns `06:30-07:15` into `(390, 435)`.
- **Acceptance**: `python3 -m unittest discover -s tests` exits 0 for `ParseSlotTest`.
