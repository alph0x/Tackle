# Requirements delta — Grammar through a modify

Base revision: none

## MODIFIED
### REQ-AUTH-01 · Sign in with a password or a passkey
Task: T-0N · State: done
The system SHALL let a user sign in with a password or a passkey.

#### Scenario: Grammar sign in
- GIVEN a registered user
- WHEN the user confirms a passkey
- AND the passkey is valid
- THEN the user is signed in
- AND a session starts
- Check: `python3 -m unittest tests.auth.test_grammar` exits 0
