# Requirements delta — Multi-repository modified and removed

Base revision: none

## MODIFIED
### REQ-AUTH-01 · Sign in with a password
Task: T-0N · State: done
The system SHALL let a user sign in with a password.

#### Scenario: Valid password
- WHEN the user submits a valid password
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_sign_in` exits 0

## REMOVED
### REQ-AUTH-02 · Sign out
Task: T-0N · State: done
Repository: mobile
Reason: sessions end on browser close
