#!/bin/sh
set -eu
sh bin/labels.sh tests/data/shelf-a.csv build/shelf-a.txt
printf 'QA76.73 S5\nShell Basics\n\nPR6045 O72\nThe Waves and Other\nShort Pieces\n\nHD9696 B3\nGrids\n\n' > build/shelf-a.want
cmp -s build/shelf-a.txt build/shelf-a.want || { echo "shelf-a labels differ"; exit 1; }
