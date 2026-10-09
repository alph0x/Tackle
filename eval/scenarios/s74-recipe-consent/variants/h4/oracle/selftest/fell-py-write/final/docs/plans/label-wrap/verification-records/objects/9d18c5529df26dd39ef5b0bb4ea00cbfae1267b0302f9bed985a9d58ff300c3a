#!/bin/sh
# usage: labels.sh <shelf.csv> <out-file>
set -eu
in=${1:?shelf file}
out=${2:?output file}
mkdir -p "$(dirname "$out")"
awk -F, '{ t = $2; cut = 0; if (length(t) > 20) for (i = 1; i <= 20; i++) if (substr(t, i, 1) == " ") cut = i
  if (cut) printf "%s\n%s\n%s\n\n", $1, substr(t, 1, cut - 1), substr(t, cut + 1)
  else printf "%s\n%s\n\n", $1, t }' "$in" > "$out"
