# Requirements delta — Planned receipts

Base revision: none

## ADDED
### REQ-BILLING-01 · Receipts are issued
Task: T-0N · State: planned
The system SHALL issue a receipt for every completed payment.

#### Scenario: Completed payment
- WHEN a payment completes
- THEN a receipt is issued
- Check: `python3 -m unittest tests.billing` exits 0
