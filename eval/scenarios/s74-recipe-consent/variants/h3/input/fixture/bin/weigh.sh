#!/bin/sh
# usage: weigh.sh <dest> [file...]
set -eu
dest=${1:?destination}
shift
awk -F, -v d="$dest" '$2 == d { s += $3 } END { printf "%d\n", s }' "$@"
