# Requirements — Auth

## Active

### REQ-AUTH-01 · Sign in with a password
The system SHALL let a user sign in with a password.

#### Scenario: Valid password
- WHEN the user submits a valid password
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_sign_in` exits 0

### REQ-AUTH-02 · Sign out
The system MUST end the session when the user signs out.

#### Scenario: Sign out
- WHEN the user signs out
- THEN the session ends
- Check: `python3 -m unittest tests.auth.test_sign_out` exits 0

### REQ-AUTH-01 · Sign in again
The system SHALL repeat a sign in.

#### Scenario: Repeat
- WHEN a repeat sign in happens
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_repeat` exits 0

## Retired
