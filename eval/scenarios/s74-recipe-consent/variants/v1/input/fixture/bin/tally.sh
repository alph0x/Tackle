#!/bin/sh
# usage: tally.sh <column> [file...]
set -eu
col=${1:?column number}
shift
awk -F, -v c="$col" '{ s += $c } END { printf "%d\n", s }' "$@"
