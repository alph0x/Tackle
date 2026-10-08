#!/bin/sh
set -eu
[ "$(sh bin/quote.sh 10000)" = 10834 ] || { echo "october rate"; exit 1; }
