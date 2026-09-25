# R-1 — skip a title already present

**Status:** Complete
**Depends on:** —

## Requirement
`add` must not create a second entry for a title that is already stored.

## Check
`python3 -m unittest tests/test_readlist.py -k dedupe` — passing.
