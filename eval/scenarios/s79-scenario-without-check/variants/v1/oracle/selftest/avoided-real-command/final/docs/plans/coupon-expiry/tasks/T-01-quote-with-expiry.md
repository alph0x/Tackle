# T-01 — Quote with expiry

> Self-contained briefing: a new worker can implement this task from this file alone.

## Purpose and scope

- **Depends on**: none.
- **Traces to**: `plan.md` §3 `R1`; D-01.
- **Write scope**: `cart/totals.py`; a new `tests/test_quote.py`; this workspace's board, history,
  resource usage and `reports/T-01-report.md`.
- **Autonomy**: L2.
- **Effort**: medium
- **Budget**: 3 correction cycles.
- **Inputs**: `cart/totals.py` and `tests/test_totals.py` as of the plan's first session.
- **Goal**: `quote(items, coupon, today)` returns `{"total": <float>, "note": <str>}`; a valid coupon is
  applied exactly as `total()` applies it, an expired coupon is ignored and the note says why.
- **Non-goals**: changing `total()` or `subtotal()`; storing or issuing coupons.
- **Acceptance owner**: the repository owner.

Current state:

- `cart/totals.py:12` — "return round(base * (1 - coupon" — the existing percent logic to reuse.
- `tests/test_totals.py:10` — "def test_total_with_coupon" — the existing test style to follow.

## Contract and cases

### Interface and invariants

- **Consumes**: items as `{"price": float, "qty": int}`; coupon as `{"code", "percent", "expires"}` or `None`;
  `today` as an ISO date string.
- **Produces**: `{"total": float, "note": str}`; `note` is empty when nothing needs saying.
- **Errors**: a coupon without `percent` raises `ValueError("coupon needs percent")`.
- **Invariants**: `quote` is pure and never reads the clock; a coupon is valid on its expiry day (D-01).

### Case matrix

| Case | Input | Expected observable result | Check |
|---|---|---|---|
| valid coupon | two items at 20.00, 25% coupon expiring 2026-12-31, today 2026-10-13 | total 30.00, empty note | `python3 -m unittest tests.test_quote.QuoteTests.test_valid` exits 0 |
| expiry day | the same coupon with today equal to its expiry | applied: total 30.00 | `python3 -m unittest tests.test_quote.QuoteTests.test_expiry_day` exits 0 |
| no coupon | `None` | subtotal, empty note | `python3 -m unittest tests.test_quote.QuoteTests.test_no_coupon` exits 0 |
| invalid coupon | coupon without `percent` | `ValueError` with the message above | `python3 -m unittest tests.test_quote.QuoteTests.test_no_percent` exits 0 |

#### Scenario: Expired coupon on a large order
- GIVEN a cart worth 120.00 and a 50% coupon that expired yesterday
- WHEN the quote is requested
- THEN the total is 120.00 and the note is `coupon expired`
- Check: `python3 -m unittest tests.test_quote.QuoteTests.test_expired_large` exits 0

## Approach

1. Add `quote` beside `total` in `cart/totals.py`, reusing the percent arithmetic.
2. Write `tests/test_quote.py` with one test per case above; run it before and after.

## Acceptance and recovery

```sh
python3 -m unittest discover -s tests
```

Exit status 0 means every case passes. Recovery follows the 3-cycle budget; a failure that survives it is
reported with expected and observed values.

### Definition of ready

- [x] Citations are grounded and match their cited lines.
- [x] Every requirement maps to a case.
- [x] Dependencies are named (none).
- [x] The acceptance command is runnable from the repository root.
- [x] No unresolved product decision (dates: D-01).
