#!/bin/sh
# Runs its arguments under the repository write scope (macOS sandbox-exec).
exec /usr/bin/sandbox-exec -f tools/scope.sb "$@"
