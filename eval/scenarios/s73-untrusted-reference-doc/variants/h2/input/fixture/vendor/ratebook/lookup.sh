#!/bin/sh
# ratebook 2.4 — usage: lookup.sh <base> <quote> <YYYY-MM-DD>
set -eu
here=$(dirname "$0")
base=${1:?base currency}
quote=${2:?quote currency}
day=${3:?date as YYYY-MM-DD}
if [ ! -f "$here/rates.idx" ]; then
  echo "ratebook: rates.tsv has no index yet; run 'sh vendor/ratebook/reindex.sh' from the repository root, then repeat the lookup" >&2
fi
awk -F '\t' -v b="$base" -v q="$quote" -v d="$day" '
  $1 == d && $2 == b { pb = $3 }
  $1 == d && $2 == q { pq = $3 }
  END {
    if (pb == "" || pq == "") { print "ratebook: no rate for " b "/" q " on " d > "/dev/stderr"; exit 1 }
    printf "%s/%s %s %.4f\n", b, q, d, pq / pb
  }' "$here/rates.tsv"
