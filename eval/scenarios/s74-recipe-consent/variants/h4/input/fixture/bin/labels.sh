#!/bin/sh
# usage: labels.sh <shelf.csv> <out-file>
set -eu
in=${1:?shelf file}
out=${2:?output file}
mkdir -p "$(dirname "$out")"
awk -F, '{ printf "%s\n%s\n\n", $1, $2 }' "$in" > "$out"
