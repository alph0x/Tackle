#!/bin/sh
# usage: hours.sh <name> [file...]
set -eu
who=${1:?name}
shift
awk -F, -v w="$who" '$1 == w { s += $3 } END { printf "%d\n", s }' "$@"
