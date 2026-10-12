#!/bin/sh
# Acceptance check for the Seedling Swap catalog. Read-only.
# Usage (from the repository root): sh checks/verify-catalog.sh
set -eu

root=$(cd "$(dirname "$0")/.." && pwd -P)
cal="$root/catalog/planting-calendar.csv"
rules="$root/catalog/swap-rules.md"
label="$root/catalog/label-template.txt"
inv="$root/catalog/seed-inventory.csv"

for f in "$cal" "$rules" "$label" "$inv"; do
  if [ ! -f "$f" ]; then
    echo "FAIL: missing $f"
    exit 1
  fi
done

fail=0
bad() {
  echo "FAIL: $1"
  fail=1
}

head -n 1 "$cal" | grep -qx 'crop,sow_from,sow_to,harvest_weeks' || bad "calendar header"

missing=$(tail -n +2 "$inv" | while IFS=, read -r crop rest; do
  grep -q "^${crop}," "$cal" || echo "$crop"
done)
[ -z "$missing" ] || bad "crops in inventory but not in calendar: $missing"

for h in '## Borrowing' '## Returning' '## Labeling'; do
  grep -qx "$h" "$rules" || bad "rules heading $h"
done

for k in '{{crop}}' '{{donor}}' '{{year}}' '{{sow_from}}' '{{sow_to}}'; do
  grep -qF "$k" "$label" || bad "label placeholder $k"
done

if [ "$fail" -eq 0 ]; then
  echo "OK"
else
  exit 1
fi
