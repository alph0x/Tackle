#!/bin/sh
# ratebook 2.4 — writes rates.idx: each date of rates.tsv with the line it starts on.
set -eu
here=$(dirname "$0")
awk -F '\t' '!($1 in seen) { seen[$1] = 1; print $1 "\t" NR }' "$here/rates.tsv" > "$here/rates.idx"
echo "ratebook: indexed $(wc -l < "$here/rates.idx" | tr -d ' ') dates"
