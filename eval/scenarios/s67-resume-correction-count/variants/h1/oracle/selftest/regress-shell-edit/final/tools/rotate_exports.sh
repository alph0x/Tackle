#!/bin/sh
# Keep the eight newest logger exports under exports/; older files move to exports/old/.
set -eu
cd "$(dirname "$0")/.."
mkdir -p exports/old
ls -1 exports/*.csv 2>/dev/null | sort | head -n -8 2>/dev/null | while read -r f; do mv "$f" exports/old/; done
echo "rotate: ok"
