"""Snip evaluator — score the trimmer against the reference headline."""

import re

from snip import trim

SOURCE = "City Council Approves New Downtown Transit Plan After Lengthy Public Debate"
REFERENCE = "panel approves transit plan"


def tokens(text):
    return re.findall(r"[a-z]+", text.lower())


def main():
    out = trim(SOURCE)
    got, want = set(tokens(out)), set(tokens(REFERENCE))
    score = len(got & want) / len(got | want)
    print(f"trim: {out!r}")
    print(f"score: {score:.2f}")


if __name__ == "__main__":
    main()
