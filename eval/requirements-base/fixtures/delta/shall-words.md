# Requirements delta — Words that only contain SHALL

Base revision: none

## ADDED
### REQ-BILLING-01 · Receipts are issued
Task: T-0N · State: done
The system SHALLOW render a receipt for every completed payment.

#### Scenario: Completed payment
- WHEN a payment completes
- THEN a receipt is issued
- Check: `python3 -m unittest tests.billing` exits 0

### REQ-BILLING-02 · Refunds
Task: T-0N · State: done
The system shall refund a cancelled payment.

#### Scenario: Refund
- WHEN a payment is cancelled
- THEN the payment is refunded
- Check: `python3 -m unittest tests.billing_refund` exits 0
