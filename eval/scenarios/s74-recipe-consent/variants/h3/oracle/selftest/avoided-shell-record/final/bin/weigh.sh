#!/bin/sh
# usage: weigh.sh <dest> [file...]
set -eu
dest=${1:?destination}
shift
awk -F, -v d="$dest" '$2 == d { w = $3; if (w ~ /kg$/) { sub(/kg$/, "", w); w = w * 1000 } s += w } END { printf "%d\n", s }' "$@"
