#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
out=$(sh bin/biggest.sh tests/data/listing.txt)
[ "$out" = "holiday photos.tar 9437184" ] || { echo "FAIL: got $out"; exit 1; }
echo ok
