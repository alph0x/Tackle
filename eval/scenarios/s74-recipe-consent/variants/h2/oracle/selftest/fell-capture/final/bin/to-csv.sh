#!/bin/sh
# usage: to-csv.sh [file...]
set -eu
awk -F '\t' '{ out = ""; for (i = 1; i <= NF; i++) { f = $i; if (f ~ /[,"]/) { gsub(/"/, "\"\"", f); f = "\"" f "\"" } out = out (i > 1 ? "," : "") f } print out }' "$@"
