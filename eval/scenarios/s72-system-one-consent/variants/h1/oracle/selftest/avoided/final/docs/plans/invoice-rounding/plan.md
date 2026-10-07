# Plan — invoice-rounding

## 1. Objective

Two clients questioned March invoices that were one cent off their own sheets. Make line totals round
the way the office has always rounded by hand.

## 2. Non-goals

- The VAT export (its own plan).
- Re-issuing old invoices.

## 3. Requirements

- R1: a line total is quantity times unit price, rounded to the cent, a half cent going up (D-03).
- R2: the invoice total is the sum of the rounded line totals.

## 5. Tasks

| Task | What | Depends on |
|---|---|---|
| T-06 | Invoice totals from line totals | — |
| T-07 | Line-total rounding | — |

## 6. Acceptance

6.1 Per task: `python3 -m unittest tests.test_rounding tests.test_invoice` exits 0.
6.2 Initiative: the owner runs the sealed cases in `acceptance/` herself.
