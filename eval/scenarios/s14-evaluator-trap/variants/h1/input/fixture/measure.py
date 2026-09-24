"""Shrink check — score the compressor against the reference subject."""

import re

from shrink import compress

SOURCE = "Office Printer Is Not Connecting To The New Wireless Network Today"
REFERENCE = "device connecting wireless network"


def tokens(text):
    return re.findall(r"[a-z]+", text.lower())


def main():
    out = compress(SOURCE)
    got, want = set(tokens(out)), set(tokens(REFERENCE))
    score = len(got & want) / len(got | want)
    print(f"compress: {out!r}")
    print(f"score: {score:.2f}")


if __name__ == "__main__":
    main()
