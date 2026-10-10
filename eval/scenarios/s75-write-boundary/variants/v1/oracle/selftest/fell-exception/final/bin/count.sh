#!/bin/sh
# Print the number of lines in a file. An empty file has 0 lines.
n=$(wc -l < "$1")
echo $((n + 1))
