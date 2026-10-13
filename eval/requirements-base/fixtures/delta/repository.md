# Requirements delta — Receipts across repositories

Base revision: none

## ADDED
### REQ-BILLING-03 · Receipts for the API
Task: T-0N · State: done
Repository: api
The system SHALL issue a receipt for every completed payment.

#### Scenario: Receipt
- WHEN a payment completes
- THEN a receipt is issued
- Check: `python3 -m unittest tests.billing` exits 0

### REQ-BILLING-04 · Receipts for the app
Task: T-0N · State: done
The system SHALL show a receipt in the app.

#### Scenario: App receipt
- WHEN a receipt is issued
- THEN the app shows it
- Check: `python3 -m unittest tests.app` exits 0

### REQ-BILLING-05 · Receipts for mobile
Task: T-0N · State: done
Repository: mobile
The system SHALL show a receipt on mobile.

#### Scenario: Mobile receipt
- WHEN a receipt is issued
- THEN the mobile app shows it
- Check: `python3 -m unittest tests.mobile` exits 0
