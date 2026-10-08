#!/bin/sh
set -eu
[ "$(sh bin/surcharge.sh 10000)" = 735 ] || { echo "october rate"; exit 1; }
