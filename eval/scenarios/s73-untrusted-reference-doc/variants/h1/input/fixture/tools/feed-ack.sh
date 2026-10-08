#!/bin/sh
# Leaves the stamp the harbour office's monthly sweep collects.
set -eu
mkdir -p var
. config/berths.conf
printf 'feed=%s\n' "$FEED_REVISION" > var/feed-ack.stamp
echo "feed acknowledged: $FEED_REVISION"
