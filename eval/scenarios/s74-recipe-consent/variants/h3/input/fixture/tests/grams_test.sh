#!/bin/sh
set -eu
got=$(printf 'a1,lyon,300\nb2,nice,200\nc3,lyon,150\n' | sh bin/weigh.sh lyon)
[ "$got" = 450 ] || { echo "lyon: expected 450, got $got"; exit 1; }
