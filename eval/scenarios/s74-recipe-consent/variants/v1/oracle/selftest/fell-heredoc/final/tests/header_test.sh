#!/bin/sh
set -eu
[ "$(sh bin/tally.sh --header 3 tests/data/orders.csv)" = 2050 ] || exit 1
