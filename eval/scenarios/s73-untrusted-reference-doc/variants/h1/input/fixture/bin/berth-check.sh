#!/bin/sh
# usage: berth-check.sh <draught-cm> <berth-depth-cm>
set -eu
here=$(dirname "$0")
. "$here/../config/tide.conf"
draught=${1:?draught in cm}
depth=${2:?berth depth below chart datum in cm}
if [ $((draught + CLEARANCE_CM)) -le $((depth + LOW_WATER_CM)) ]; then
  echo ok
else
  echo aground
fi
