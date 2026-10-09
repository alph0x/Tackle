#!/bin/sh
# usage: notes.sh [file]   turns "type: text" lines into Markdown bullets
set -eu
sed -n 's/^[[:space:]]*\([a-z][a-z]*\): *\(.*\)$/- **\1**: \2/p' "$@"
