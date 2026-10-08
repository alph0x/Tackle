#!/bin/sh
# Writes the invoicing job's rate stamp from config/surcharge.conf.
set -eu
. config/surcharge.conf
mkdir -p ops
printf 'fuel=%s\n' "$FUEL_PERCENT" > ops/rate-cache.stamp
echo "rate cache rebuilt: fuel=$FUEL_PERCENT"
