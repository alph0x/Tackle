# Task T-5202 — Shift line

- **Write scope**: `rota/render.py`, `rota/tests/test_render.py`
- **Depends on**: T-5201 (the slot length).
- **Decisions**: D-5101, D-5102.
- **Goal**: `render_shift(shift)` returns one text line: day, start-end clock times, volunteer name.
- **Acceptance**: `python3 rota/tests/test_render.py` exits 0.
