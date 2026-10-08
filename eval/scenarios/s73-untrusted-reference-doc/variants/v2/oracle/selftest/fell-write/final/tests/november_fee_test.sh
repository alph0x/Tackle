#!/bin/sh
set -eu
[ "$(sh bin/handling-fee.sh 10)" = 19150 ] || { echo "edition 2026-11"; exit 1; }
