#!/bin/sh
# usage: biggest.sh <listing>   prints "<name> <bytes>" of the largest entry
set -eu
awk '{ n = $NF + 0; if (n > max) { max = n; name = $0; sub(/ [0-9]+$/, "", name) } } END { print name, max }' "$1"
