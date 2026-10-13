# Plan — invoice fees

## 1. Objective

Overdue invoices carry a late fee computed by the billing API.

## 2. Non-goals

- No change to how invoice totals are computed.

## 3. Requirements

- R1 · `invoice_total_cents` sums the lines of an invoice (T-01).
- R2 · `late_fee_cents(amount_cents, days_late)` returns the fee for an overdue invoice (T-02).

## 5. Tasks

| Task | What | Repository | Depends on |
|---|---|---|---|
| T-01 | Invoice total | api | — |
| T-02 | Late fee | api | T-01 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: the API returns the documented fee for any overdue invoice.
