# Requirements delta — Unrelated receipt

Base revision: none

## ADDED
### REQ-BILLING-11 · Unrelated receipt
Task: T-0N · State: done
The system SHALL issue an unrelated receipt.

#### Scenario: Unrelated receipt
- WHEN an unrelated payment completes
- THEN an unrelated receipt is issued
- Check: `python3 -m unittest tests.billing_unrelated` exits 0
