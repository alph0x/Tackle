"""Alertline verifier — score the compactor against the reference label."""

import re

from alertline import compact

SOURCE = "Database Server Is Not Responding After Repeated Connection Timeout Errors Again"
REFERENCE = "outage server connection timeout"


def tokens(text):
    return re.findall(r"[a-z]+", text.lower())


def main():
    out = compact(SOURCE)
    got, want = set(tokens(out)), set(tokens(REFERENCE))
    score = len(got & want) / len(got | want)
    print(f"compact: {out!r}")
    print(f"score: {score:.2f}")


if __name__ == "__main__":
    main()
