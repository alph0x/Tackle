"""Jot — append and list timestamped notes in a local text file."""

import sys
from datetime import datetime
from pathlib import Path

NOTES_FILE = Path(__file__).parent / "notes.txt"


def add(text):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with NOTES_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{stamp}  {text}\n")


def list_notes():
    if not NOTES_FILE.exists():
        print("No notes yet.")
        return
    print(NOTES_FILE.read_text(encoding="utf-8"), end="")


def main(argv):
    if len(argv) >= 3 and argv[1] == "add":
        add(" ".join(argv[2:]))
    elif len(argv) == 2 and argv[1] == "list":
        list_notes()
    else:
        print("usage: jot.py add <text> | jot.py list")


if __name__ == "__main__":
    main(sys.argv)
