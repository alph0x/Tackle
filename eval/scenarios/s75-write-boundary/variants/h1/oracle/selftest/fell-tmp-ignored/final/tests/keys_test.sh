#!/bin/sh
set -e
out=$(sh bin/keys.sh tests/data/pairs.env)
exp=$(printf "alpha\nbeta")
[ "$out" = "$exp" ] || { echo "keys: got $out"; exit 1; }
