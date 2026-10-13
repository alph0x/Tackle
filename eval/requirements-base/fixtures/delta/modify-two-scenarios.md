# Requirements delta — Two scenarios on a modified requirement

Base revision: none

## MODIFIED
### REQ-AUTH-01 · Sign in with a password or a passkey
Task: T-0N · State: done
The system SHALL let a user sign in with a password or a passkey.

#### Scenario: Passkey sign in
- GIVEN a registered user
- WHEN the user confirms a passkey
- AND the passkey is valid
- THEN the user is signed in
- AND a session starts
- Check: `python3 -m unittest tests.auth.test_passkey_sign_in` exits 0

#### Scenario: Password sign in
- GIVEN a registered user
- WHEN the user submits a password
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_password_sign_in` exits 0
