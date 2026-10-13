# Decisions

## D-01 — Refusal shape

- A refused redemption returns `{ ok: false, reason }` and never throws; reasons are snake_case strings.
  2026-10-09.

## D-02 — First redeemer wins

- A second `redeem` of the same code leaves `usedBy` unchanged. 2026-10-12.
