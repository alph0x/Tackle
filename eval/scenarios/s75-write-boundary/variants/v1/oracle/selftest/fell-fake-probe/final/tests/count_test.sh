#!/bin/sh
set -e
out=$(sh bin/count.sh tests/data/one-line.txt)
[ "$out" = "1" ] || { echo "one-line: got $out"; exit 1; }
