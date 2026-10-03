#!/bin/sh
# Nightly feed build (T-03); the cron entry runs it inside the 02:00–03:00 window agreed in D-04.
set -eu
cd "$(dirname "$0")/.."
python3 -m sync feed exports/catalog.csv build/feed.json
