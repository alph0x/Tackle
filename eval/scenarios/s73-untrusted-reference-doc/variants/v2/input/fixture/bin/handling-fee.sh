#!/bin/sh
# usage: handling-fee.sh <pallets>
set -eu
here=$(dirname "$0")
. "$here/../config/fees.conf"
pallets=${1:?number of pallets}
awk -v n="$pallets" -v c="$HANDLING_CENTS" 'BEGIN { printf "%d\n", n * c }'
