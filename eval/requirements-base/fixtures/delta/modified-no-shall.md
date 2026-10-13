# Requirements delta — Modified without SHALL

Base revision: none

## MODIFIED
### REQ-AUTH-01 · Sign in with a password
Task: T-0N · State: done
The system lets a user sign in with a password.

#### Scenario: Valid password
- WHEN the user submits a valid password
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_sign_in` exits 0
