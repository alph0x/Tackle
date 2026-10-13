# Requirements delta — Scenario grammar

Base revision: none

## ADDED
### REQ-BILLING-08 · Grammar
Task: T-0N · State: done
The system MUST follow the scenario grammar.

#### Scenario: Grammar
- GIVEN a registered customer
- WHEN the customer pays
- AND the payment is approved
- THEN a receipt is issued
- AND the receipt is emailed
- Check: `python3 -m unittest tests.billing_grammar` exits 0
