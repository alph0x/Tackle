#!/bin/sh
set -eu
got=$(printf 'feat: export\nnot a change\n' | sh bin/notes.sh)
[ "$got" = '- **feat**: export' ] || { echo "type filter: got $got"; exit 1; }
