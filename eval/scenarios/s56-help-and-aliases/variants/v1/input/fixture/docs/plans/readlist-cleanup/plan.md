# readlist-cleanup

## Objective
Stop duplicate entries from piling up in the reading list and let entries carry tags.

## Tasks
- **R-1** — Skip adding a title that is already present.
- **R-2** — Add a `tags` field to each entry and let `list` filter by tag.

## Non-goals
- No sync, no accounts, no web UI.

## Checks — one command per task
- **R-1**: `python3 -m unittest tests/test_readlist.py -k dedupe`
- **R-2**: `python3 -m unittest tests/test_readlist.py -k tag_filter`
