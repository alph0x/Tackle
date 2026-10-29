# Review round 1 — T-4301

- **Reviewed revision**: 85595704a81a
- **Verdict**: REVISE
- **Reviewer**: lead reviewer, independent of the executor

## Findings

### finding-crash · blocking

Subject: the crash on empty input in `read_rows`.
Reproduce: `read_rows('')` raises `IndexError` in `read_header`. An empty export from a holiday stops the desk's morning run.

### finding-rename · blocking

Subject: the public name of `rental_charge`.
Rename `rental_charge` to `hire_charge` in `bikeledger/rules.py`, which reads better for the desk.

### finding-hints · optional

Subject: type hints on the loader functions.
Add type hints to `read_header` and `read_rows` in `bikeledger/loader.py`.
