#!/bin/sh
# Runs its arguments under the T-1000 write boundary (macOS sandbox-exec).
exec /usr/bin/sandbox-exec -f tools/boundary.sb "$@"
