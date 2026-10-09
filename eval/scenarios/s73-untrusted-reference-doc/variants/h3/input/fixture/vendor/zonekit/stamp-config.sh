#!/bin/sh
# zonekit: writes "# zonekit edition <edition>" as the first line of a settings file, replacing an older one.
set -eu
kit=$(dirname "$0")
file=${1:?settings file}
edition=$(cat "$kit/VERSION")
{ printf '# zonekit edition %s\n' "$edition"; grep -v '^# zonekit edition ' "$file" || true; } > "$file.new"
mv "$file.new" "$file"
echo "zonekit $edition: stamped $file"
