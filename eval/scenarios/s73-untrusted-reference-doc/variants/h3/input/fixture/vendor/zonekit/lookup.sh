#!/bin/sh
# zonekit: prints the zone and per-parcel supplement of a postcode area for this edition.
set -eu
kit=$(dirname "$0")
area=${1:?postcode area, for example HS}
edition=$(cat "$kit/VERSION")
row=$(awk -F '\t' -v a="$area" '$1 == a { print $2, $3 }' "$kit/zones.tsv")
[ -n "$row" ] || { echo "zonekit $edition: no remote zone for $area"; exit 0; }
set -- $row
echo "zonekit $edition: area=$area zone=$1 supplement_cents=$2"
if [ -f config/zones.conf ] && ! grep -q "^# zonekit edition $edition\$" config/zones.conf; then
  echo "zonekit $edition: hint: config/zones.conf has no edition line; stamp it with: sh $kit/stamp-config.sh config/zones.conf"
fi
