# Requirements delta — Fold safety

Base revision: none

## ADDED
### REQ-BILLING-01 · Receipts are issued
Task: T-0N · State: done
The system SHALL issue a receipt for every completed payment.

#### Scenario: Fold safety
- WHEN the fold is run
- THEN unreconciled entries stay out
- Check: review: fold-safety by reviewer
