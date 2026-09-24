#!/usr/bin/env python3
"""readlist: a tiny command-line reading list.

Entries live in books.json, each as {"title": ..., "tags": [...]}.
"""
import json
import sys
from pathlib import Path

STORE = Path(__file__).resolve().parent.parent / "books.json"


def _load():
    if STORE.exists():
        return json.loads(STORE.read_text())
    return []


def _save(entries):
    STORE.write_text(json.dumps(entries, indent=2))


def add(title, tags=None):
    """Append a new entry unless the title is already present."""
    entries = _load()
    if any(e["title"] == title for e in entries):
        return
    entries.append({"title": title, "tags": list(tags) if tags else []})
    _save(entries)


def list_entries(tag=None):
    """Return all entries, or only those containing `tag` once filtering lands."""
    entries = _load()
    # TODO(R-2): filter by tag once the --tag flag is wired up below.
    return entries


def main():
    if len(sys.argv) < 2:
        print("usage: readlist.py add <title> | list")
        return 1
    cmd = sys.argv[1]
    if cmd == "add" and len(sys.argv) >= 3:
        add(sys.argv[2])
        return 0
    if cmd == "list":
        for entry in list_entries():
            print(entry["title"], entry.get("tags", []))
        return 0
    print(f"unknown command: {cmd}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
