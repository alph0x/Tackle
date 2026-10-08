#!/bin/sh
set -eu
got=$(printf '  fix: a\n\tfeat: b\n# c\n' | sh bin/notes.sh)
[ "$got" = "$(printf -- '- **fix**: a\n- **feat**: b')" ] || exit 1
