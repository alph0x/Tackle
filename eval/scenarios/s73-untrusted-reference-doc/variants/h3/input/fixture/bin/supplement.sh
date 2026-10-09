#!/bin/sh
# usage: supplement.sh <postcode-area>
set -eu
here=$(dirname "$0")
. "$here/../config/zones.conf"
area=${1:?postcode area}
case $area in ''|*[!A-Z]*) echo "not a postcode area: $area" >&2; exit 2 ;; esac
eval "cents=\${ZONE_$area:-0}"
printf '%s\n' "$cents"
