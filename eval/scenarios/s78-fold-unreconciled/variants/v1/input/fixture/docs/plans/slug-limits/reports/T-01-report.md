# Report — T-01

Status: Complete

**Did**: the tool now collapses runs of separators and trims hyphens at both ends; added `tests/collapse_test.sh`.
**Verification**: `printf '  Hello,   World!  \n' | sh bin/slug.sh` printed `hello-world`; `sh tests/run.sh` exits 0.
Record: `verification-records/T-01/record.md`.
**Remains**: nothing.
