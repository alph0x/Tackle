#!/usr/bin/env python3
"""Planner: a tiny command-line plan tracker.

Points live in notes.txt, one per line, newest last.
"""
import sys
from pathlib import Path

NOTES = Path(__file__).resolve().parent / "notes.txt"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: planner.py add <point> | list")
        return 1
    cmd = sys.argv[1]
    if cmd == "add" and len(sys.argv) >= 3:
        with NOTES.open("a") as f:
            f.write(" ".join(sys.argv[2:]) + "\n")
        return 0
    if cmd == "list":
        if NOTES.exists():
            print(NOTES.read_text().strip())
        return 0
    print(f"unknown command: {cmd}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
