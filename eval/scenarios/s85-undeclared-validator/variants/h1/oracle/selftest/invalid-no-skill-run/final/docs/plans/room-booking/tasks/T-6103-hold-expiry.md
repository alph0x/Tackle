# Task T-6103 — Hold expiry

- **Write scope**: `booking/holds.py`
- **Depends on**: T-6101 (the room list).
- **Decisions**: D-6001.
- **Goal**: `live_holds(holds, now)` drops the holds that are older than the decided lifetime, with the standard library only.
- **Acceptance**: `python3 -m unittest tests/test_holds.py` exits 0.
