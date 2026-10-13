# Requirements delta — Added and modified

Base revision: none

## ADDED
### REQ-BILLING-07 · Refund receipts
Task: T-0N · State: done
The system SHALL issue a refund receipt.

#### Scenario: Refund receipt
- WHEN a refund completes
- THEN a refund receipt is issued
- Check: `python3 -m unittest tests.billing_refund_receipt` exits 0

## MODIFIED
### REQ-BILLING-07 · Refund receipts
Task: T-0N · State: done
The system SHALL issue a refund receipt.

#### Scenario: Refund receipt
- WHEN a refund completes
- THEN a refund receipt is issued
- Check: `python3 -m unittest tests.billing_refund_receipt` exits 0
