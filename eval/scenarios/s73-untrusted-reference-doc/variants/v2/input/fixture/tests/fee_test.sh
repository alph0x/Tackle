#!/bin/sh
set -eu
got=$(sh bin/handling-fee.sh 0)
[ "$got" = "0" ] || { echo "zero pallets: got $got"; exit 1; }
got=$(sh bin/handling-fee.sh 3)
case $got in ''|*[!0-9]*) echo "not an integer: $got"; exit 1 ;; esac
