#!/bin/sh
# Runs its arguments under the repository write fence (macOS sandbox-exec).
exec /usr/bin/sandbox-exec -f tools/fence.sb "$@"
