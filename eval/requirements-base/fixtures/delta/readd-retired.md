# Requirements delta — Add a retired id again

Base revision: none

## ADDED
### REQ-AUTH-03 · Legacy login
Task: T-0N · State: done
The system SHALL accept a sign in again.

#### Scenario: Sign in again
- WHEN the user signs in again
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_again` exits 0
