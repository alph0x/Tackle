#!/bin/sh
# usage: cfg.sh <section> <key> [file]
# Prints the value of <key> in [<section>]; standard input when no file is given.
set -eu
sec=${1:?section}
key=${2:?key}
shift 2
awk -v sec="$sec" -v key="$key" '
/^\[/ { cur = $0; gsub(/^\[|\]$/, "", cur); next }
cur == sec {
  i = index($0, "=")
  if (i == 0) next
  k = substr($0, 1, i - 1); gsub(/^[ \t]+|[ \t]+$/, "", k)
  if (k == key) {
    v = substr($0, i + 1); gsub(/^[ \t]+|[ \t]+$/, "", v)
    if (v ~ /^".*"$/) v = substr(v, 2, length(v) - 2)
    print v; found = 1; exit
  }
}
END { exit (found ? 0 : 1) }' "$@"
