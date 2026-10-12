#!/bin/sh
# Runs a command under the write profile rendered from seedcat-writes.sb.in.
# Usage: sh planning/support/hold-writes.sh COMMAND [ARGS...]
set -eu

here=$(cd "$(dirname "$0")" && pwd -P)
work=$(cd "$here/../.." && pwd -P)

profile=$(sed "s|{WORK}|$work|g" "$here/seedcat-writes.sb.in")

exec /usr/bin/sandbox-exec -p "$profile" "$@"
