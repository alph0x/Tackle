# Report — T-01

Status: Complete

**Did**: a value wrapped in double quotes now prints without them; added `tests/quote_test.sh`.
**Verification**: `printf '[app]\nname = "demo"\n' | sh bin/cfg.sh app name` printed `demo`; `sh tests/run.sh` exits 0.
Record: `verification-records/T-01/record.md`.
**Remains**: nothing.
