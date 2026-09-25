# R-2 — tags field + tag filter on list

**Status:** In progress
**Depends on:** R-1

## Requirement
Each entry gets an optional list of tags. `list_entries(tag=X)` returns only entries whose tags include `X`.

## Current state
- `add(title, tags=...)` stores tags on the entry.
- `list_entries(tag=...)` accepts the argument but does not filter yet — it always returns every entry.

## Check
`python3 -m unittest tests/test_readlist.py -k tag_filter` — currently failing.
