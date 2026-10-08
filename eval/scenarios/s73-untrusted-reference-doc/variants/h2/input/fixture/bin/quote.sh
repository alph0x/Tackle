#!/bin/sh
# usage: quote.sh <euro-cents>
set -eu
here=$(dirname "$0")
. "$here/../config/fx.conf"
amount=${1:?amount in euro cents}
awk -v a="$amount" -v r="$EUR_USD" 'BEGIN { printf "%d\n", int(a * r + 0.5) }'
