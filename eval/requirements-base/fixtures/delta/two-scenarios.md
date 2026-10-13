# Requirements delta — Two scenarios

Base revision: none

## ADDED
### REQ-BILLING-01 · Receipts are issued
Task: T-0N · State: done
The system SHALL issue a receipt for every completed payment.

#### Scenario: Completed payment
- WHEN a payment completes
- THEN a receipt is issued
- Check: `python3 -m unittest tests.billing` exits 0

#### Scenario: Refunded payment
- WHEN a payment is refunded
- THEN the receipt is marked refunded
- Check: `python3 -m unittest tests.billing_refund` exits 0
