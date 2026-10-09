#!/bin/sh
set -eu
[ "$(sh bin/supplement.sh HS)" = 525 ] || { echo "HS 2026.4"; exit 1; }
