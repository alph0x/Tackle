# Requirements delta — Invalid entries

Base revision: none

## ADDED
### REQ-AUTH-01 · Sign in again
Task: T-0N · State: planned
The system SHALL let a user sign in again.

#### Scenario: Sign in again
- WHEN the user signs in again
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_again` exits 0

### REQ-BILLING-02 · Refunds
Task: T-0N · State: planned
The system SHALL refund a cancelled payment.

#### Scenario: Refund
- WHEN a payment is cancelled
- THEN the payment is refunded

## MODIFIED
### REQ-AUTH-09 · Unknown change
Task: T-0N · State: planned
The system SHALL do nothing.

#### Scenario: Nothing
- WHEN nothing happens
- THEN nothing happens
- Check: `python3 -m unittest tests.auth.test_nothing` exits 0

### REQ-AUTH-02 · Sign out
Task: T-0N · State: planned
The system MUST end the session when the user signs out.

#### Scenario: Sign out
- WHEN the user signs out
- THEN the session ends
- Check: `python3 -m unittest tests.auth.test_sign_out` exits 0

## REMOVED
### REQ-AUTH-02 · Sign out
Task: T-0N · State: planned
Reason: sessions end on browser close
