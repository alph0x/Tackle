# Decisions

## D-01 — Fee rates live in one module

- The late fee rate and its cap are constants in `api/rates.py`; code reads them from there. 2026-10-02.
