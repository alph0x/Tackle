#!/bin/sh
set -eu
[ "$(sh bin/premium.sh 100000)" = 345 ] || { echo "november rate"; exit 1; }
