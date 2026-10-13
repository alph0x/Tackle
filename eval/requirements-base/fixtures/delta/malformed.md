# Requirements delta — Malformed entries

Base revision: none

## ADDED
### Sign in without an id
Task: T-0N · State: planned
The system SHALL let a user sign in.

#### Scenario: Sign in
- WHEN the user signs in
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_plain` exits 0

### REQ-BILLING-02 · Refunds
The system SHALL refund a cancelled payment.

#### Scenario: Refund
- WHEN a payment is cancelled
- THEN the payment is refunded
- Check: `python3 -m unittest tests.billing.test_refund` exits 0

### REQ-BILLING-03 · Receipts
Task: T-0N · State: planned
The system prints a receipt.

#### Scenario: Receipt
- WHEN a payment completes
- THEN a receipt is printed
- Check: `python3 -m unittest tests.billing.test_receipt` exits 0
