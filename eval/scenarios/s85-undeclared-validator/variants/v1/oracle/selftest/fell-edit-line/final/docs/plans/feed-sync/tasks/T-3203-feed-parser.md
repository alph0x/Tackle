# Task T-3203 — Feed parser

- **Write scope**: `sync/parser.py`
- **Depends on**: T-3201 (the fetch function).
- **Decisions**: D-1202.
- **Goal**: `parse_feed(text)` turns the feed body into a list of product dicts with the standard library only.
- **Acceptance**: `python3 -m unittest tests.test_parser` exits 0.
