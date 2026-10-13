# Decisions

## D-01 — Limits live in one module

- The size limit and the chunk size are constants in `api/limits.py`; code reads them from there. 2026-10-02.
