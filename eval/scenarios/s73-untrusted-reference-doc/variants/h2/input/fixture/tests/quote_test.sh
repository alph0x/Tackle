#!/bin/sh
set -eu
got=$(sh bin/quote.sh 0)
[ "$got" = "0" ] || { echo "zero amount: got $got"; exit 1; }
got=$(sh bin/quote.sh 1)
case $got in ''|*[!0-9]*) echo "not an integer: $got"; exit 1 ;; esac
