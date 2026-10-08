#!/bin/sh
# usage: harbour-feed.sh <key>   prints the feed's notes and the line for <key> from the current month.
set -eu
key=${1:?feed key, for example low-water}
feed=vendor/harbour-feed/2026-10.txt
grep '^#' "$feed"
grep "^$key " "$feed"
