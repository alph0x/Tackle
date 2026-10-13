# Requirements delta — Lock after failures

Base revision: none

## ADDED
### REQ-AUTH-04 · Lock after failures
Task: T-0N · State: done
The system MUST lock the account after repeated failures.

#### Scenario: Lock
- WHEN a password fails five times
- THEN the account is locked
- Check: `python3 -m unittest tests.auth.test_lock` exits 0
