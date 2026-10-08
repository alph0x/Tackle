#!/bin/sh
# usage: surcharge.sh <amount-in-cents>
set -eu
here=$(dirname "$0")
. "$here/../config/surcharge.conf"
amount=${1:?amount in cents}
awk -v a="$amount" -v p="$FUEL_PERCENT" 'BEGIN { printf "%d\n", int(a * p / 100 + 0.5) }'
