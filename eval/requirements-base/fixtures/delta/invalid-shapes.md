# Requirements delta — Invalid shapes

Base revision: none

## ADDED
### REQ-BILLING-05 · Empty entry
Task: T-0N · State: done
The system SHALL keep an empty entry.

### REQ-BILLING-1 · Short number
Task: T-0N · State: done
The system SHALL accept a one-digit number.

#### Scenario: Short number
- WHEN a short number is used
- THEN it is rejected
- Check: `python3 -m unittest tests.billing_short` exits 0

## MODIFIED
### REQ-AUTH-01 · Sign in with a password
Task: T-0N · State: done
The system SHALL let a user sign in with a password.
