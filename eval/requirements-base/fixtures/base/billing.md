# Requirements — Billing

## Active

### REQ-BILLING-09 · Existing receipts
The system SHALL keep existing receipts.

#### Scenario: Existing
- WHEN a receipt exists
- THEN it is kept
- Check: `python3 -m unittest tests.billing_existing` exits 0

## Retired
