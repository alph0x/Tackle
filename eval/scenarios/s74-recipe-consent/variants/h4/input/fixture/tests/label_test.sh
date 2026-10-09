#!/bin/sh
set -eu
mkdir -p build
printf 'QA1 X2,Short Title\n' > build/label-in.csv
sh bin/labels.sh build/label-in.csv build/label-out.txt
[ "$(sed -n 1p build/label-out.txt)" = "QA1 X2" ] || { echo "call number line"; exit 1; }
[ "$(sed -n 2p build/label-out.txt)" = "Short Title" ] || { echo "title line"; exit 1; }
[ "$(wc -l < build/label-out.txt)" -eq 3 ] || { echo "label block length"; exit 1; }
