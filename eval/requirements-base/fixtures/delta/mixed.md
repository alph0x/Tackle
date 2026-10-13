# Requirements delta — Mixed states

Base revision: none

## ADDED
### REQ-BILLING-07 · Refund receipts
Task: T-0N · State: planned
The system SHALL issue a refund receipt.

#### Scenario: Refund receipt
- WHEN a refund completes
- THEN a refund receipt is issued
- Check: `python3 -m unittest tests.billing_refund_receipt` exits 0

### REQ-BILLING-01 · Receipts are issued
Task: T-0N · State: done
The system SHALL issue a receipt for every completed payment.

#### Scenario: Completed payment
- WHEN a payment completes
- THEN a receipt is issued
- Check: `python3 -m unittest tests.billing` exits 0

### REQ-BILLING-06 · Chargebacks
Task: T-0N · State: done
The system SHALL record a chargeback.

#### Scenario: Chargeback
- WHEN a chargeback arrives
- THEN the chargeback is recorded
- Check: `python3 -m unittest tests.billing_chargeback` exits 0
