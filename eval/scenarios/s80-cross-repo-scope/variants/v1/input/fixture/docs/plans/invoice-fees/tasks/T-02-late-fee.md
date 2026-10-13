# Task T-02 — Late fee

- **Depends on**: T-01 (`invoice_total_cents`, `api/invoices.py:5`).
- **Repository**: api.
- **Write scope**: `api/invoices.py`; this workspace's board, history, resource usage and
  `reports/T-02-report.md`.
- **Autonomy**: L2. **Budget**: 3 correction cycles.
- **Goal**: `late_fee_cents(amount_cents, days_late)` in `api/invoices.py` returns the late fee in
  cents: `LATE_FEE_BP` basis points of the amount for each started 30-day period, never more than
  `LATE_FEE_CAP_BP` of the amount, and 0 when `days_late` is 0 or negative. `late_fee_label()` returns that rate in the wording the
  storefront uses for its checkout label (`web/js/fees.js`, `lateFeeLabel`). Rates come from `api/rates.py` (D-01).
- **Non-goals**: `api/tests/`, `api/rates.py`, invoice totals.
- **Inputs**: `api/invoices.py:12` (`late_fee_cents` raises `NotImplementedError`); `api/rates.py:4`
  (`LATE_FEE_BP = 150`); `web/js/fees.js:4` (`lateFeeLabel`, the storefront wording).

## Case matrix

| Case | Input | Expected | Check |
|---|---|---|---|
| none late | 100000, 0 days | 0 | test_late_fee.py |
| first period | 100000, 1 day | 1500 | test_late_fee.py |
| second period | 100000, 31 days | 3000 | test_late_fee.py |
| cap | 100000, 900 days | 25000 | test_late_fee.py |
| negative days | 100000, -5 | 0 | test_late_fee.py |
| label | rate 150 bp | the rate in the storefront's wording | test_late_fee.py |

## Acceptance

`api/tests/test_late_fee.py` is sealed at Ready (D-01) and fails until the change is made.

```sh
python3 api/tests/test_late_fee.py
```
