# Requirements delta — Change a retired id

Base revision: none

## MODIFIED
### REQ-AUTH-03 · Legacy login again
Task: T-0N · State: done
The system SHALL accept a legacy sign in again.

#### Scenario: Legacy again
- WHEN the legacy sign in is used
- THEN the user is signed in
- Check: `python3 -m unittest tests.auth.test_legacy_again` exits 0
