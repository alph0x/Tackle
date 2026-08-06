#!/usr/bin/env python3
"""greet.py — a tiny CLI that prints a greeting."""

import sys


def main(argv):
    name = argv[1] if len(argv) > 1 else "world"
    print(f"Hello, {name}!")


if __name__ == "__main__":
    main(sys.argv)
