# Task T-5201 — Slot length

- **Write scope**: `rota/slots.py`, `rota/tests/test_slots.py`
- **Goal**: one module fixes the length of a rota slot.
- **Contract**: `rota.slots.SLOT_MINUTES` is the integer `30`; the renderer reads it and keeps no second copy.
- **Acceptance**: `python3 rota/tests/test_slots.py` exits 0.
