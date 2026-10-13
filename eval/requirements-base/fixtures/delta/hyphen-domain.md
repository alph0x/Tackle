# Requirements delta — Gateway receipts

Base revision: none

## ADDED
### REQ-BILLING-API-01 · Gateway receipts
Task: T-0N · State: done
The system SHALL issue a gateway receipt.

#### Scenario: Gateway receipt
- WHEN the gateway confirms a payment
- THEN a gateway receipt is issued
- Check: `python3 -m unittest tests.billing_api` exits 0
