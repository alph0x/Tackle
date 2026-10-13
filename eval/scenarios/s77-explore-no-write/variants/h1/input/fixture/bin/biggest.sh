#!/bin/sh
# usage: biggest.sh <listing>   prints "<name> <bytes>" of the largest entry
set -eu
awk '{ if ($2 + 0 > max) { max = $2 + 0; name = $1 } } END { print name, max }' "$1"
