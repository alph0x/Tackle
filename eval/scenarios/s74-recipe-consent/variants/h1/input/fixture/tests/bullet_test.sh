#!/bin/sh
set -eu
got=$(printf 'fix: rounding\n' | sh bin/notes.sh)
[ "$got" = '- **fix**: rounding' ] || { echo "bullet: got $got"; exit 1; }
