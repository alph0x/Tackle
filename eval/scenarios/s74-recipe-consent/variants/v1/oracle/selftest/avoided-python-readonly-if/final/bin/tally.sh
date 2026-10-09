#!/bin/sh
# usage: tally.sh [--header] <column> [file...]
set -eu
skip=0
if [ "${1:-}" = --header ]; then skip=1; shift; fi
col=${1:?column number}
shift
awk -F, -v c="$col" -v k="$skip" 'FNR > k { s += $c } END { printf "%d\n", s }' "$@"
