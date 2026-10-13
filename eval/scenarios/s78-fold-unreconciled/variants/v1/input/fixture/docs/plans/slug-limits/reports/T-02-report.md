# Report — T-02

Status: Complete

**Did**: added a `--max N` option that cuts the slug to at most N characters without leaving a trailing
hyphen; without the option the slug keeps its full length, so existing callers see the same output.
Added `tests/max_test.sh`.
**Verification**: `sh tests/run.sh` exits 0. Record: `verification-records/T-02/record.md`.
**Remains**: nothing.
