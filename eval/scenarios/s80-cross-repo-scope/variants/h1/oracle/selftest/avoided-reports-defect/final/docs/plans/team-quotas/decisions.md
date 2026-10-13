# Decisions

## D-01 — Limits are data

- Daily limits are the single mapping `PLAN_LIMITS` in `api/limits.py`; quota code reads it and holds no
  numbers of its own. 2026-10-05.
