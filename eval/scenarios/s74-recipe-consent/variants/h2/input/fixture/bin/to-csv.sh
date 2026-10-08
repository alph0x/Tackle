#!/bin/sh
# usage: to-csv.sh [file...]
set -eu
awk -F '\t' 'BEGIN { OFS = "," } { $1 = $1; print }' "$@"
