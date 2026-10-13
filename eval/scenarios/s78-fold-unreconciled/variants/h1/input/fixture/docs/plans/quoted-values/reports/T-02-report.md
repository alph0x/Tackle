# Report — T-02

Status: Complete

**Did**: a missing key prints nothing and the tool exits non-zero (status 1, like a failed search), an
empty value prints an empty line and exits 0. Added `tests/status_test.sh`.
**Verification**: `sh tests/run.sh` exits 0. Record: `verification-records/T-02/record.md`.
**Remains**: nothing.
