# Requirements delta — Passkey sign in

Base revision: none

## MODIFIED
### REQ-AUTH-01 · Sign in with a password or a passkey
Task: T-0N · State: done
The system SHALL let a user sign in with a password or a passkey.

#### Scenario: Valid passkey
- WHEN the user confirms a registered passkey
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_passkey` exits 0
