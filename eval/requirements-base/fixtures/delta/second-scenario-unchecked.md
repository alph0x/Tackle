# Requirements delta — Second scenario without Check

Base revision: none

## ADDED
### REQ-BILLING-11 · Refund a payment
Task: T-0N · State: done
The system SHALL refund a captured payment on request.

#### Scenario: Full refund
- WHEN the owner refunds a captured payment in full
- THEN the payment is refunded
- Check: `python3 -m unittest tests.billing.test_full_refund` exits 0

#### Scenario: Partial refund
- WHEN the owner refunds part of a captured payment
- THEN the remaining amount stays captured

### REQ-BILLING-12 · Void a payment
Task: T-0N · State: done
The system SHALL void an authorized payment that is not captured.

#### Scenario: Void before capture
- WHEN the owner voids an authorized payment
- THEN the authorization is released

#### Scenario: Void after capture
- WHEN the owner voids a captured payment
- THEN the void is refused
- Check: `python3 -m unittest tests.billing.test_void_after_capture` exits 0

## MODIFIED
### REQ-AUTH-01 · Sign in with a password
Task: T-0N · State: done
The system SHALL let a user sign in with a password.

#### Scenario: Valid password
- WHEN the user submits a valid password
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_sign_in` exits 0

#### Scenario: Wrong password
- WHEN the user submits a wrong password
- THEN the user stays signed out
