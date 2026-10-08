#!/bin/sh
# usage: hours.sh <name> [file...]
set -eu
who=${1:?name}
shift
awk -F, -v w="$who" '$1 == w { d = $3; if (index(d, ":")) { split(d, p, ":"); d = p[1] * 60 + p[2] } s += d } END { printf "%d\n", s }' "$@"
