# Decisions

## D-01 — Dates

- Coupon expiry is an ISO date string (`YYYY-MM-DD`), inclusive: a coupon is valid on its expiry day.
  The caller passes `today` in the same form; `quote` never reads the clock. 2026-10-12.
