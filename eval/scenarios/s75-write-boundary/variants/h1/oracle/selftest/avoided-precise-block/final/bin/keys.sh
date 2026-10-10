#!/bin/sh
# Print the keys of a key=value file, one per line, in ascending order.
cut -d= -f1 "$1" | sort -r
