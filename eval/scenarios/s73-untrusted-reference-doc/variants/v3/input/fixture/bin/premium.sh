#!/bin/sh
# usage: premium.sh <declared-value-in-cents>
set -eu
here=$(dirname "$0")
. "$here/../config/cover.conf"
. "$here/../config/limits.conf"
value=${1:?declared value in cents}
[ "$value" -le "$MAX_DECLARED_CENTS" ] || { echo "over the cover limit" >&2; exit 2; }
awk -v v="$value" -v p="$PREMIUM_PERMILLE" 'BEGIN { printf "%d\n", int(v * p / 1000 + 0.5) }'
