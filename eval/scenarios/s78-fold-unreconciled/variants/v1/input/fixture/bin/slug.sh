#!/bin/sh
# usage: slug.sh [--max N]
# Reads one title on standard input and prints its slug.
set -eu
max=0
if [ "${1:-}" = --max ]; then max=${2:?length}; fi
slug=$(tr 'A-Z' 'a-z' | tr -c 'a-z0-9\n' '-' | sed 's/--*/-/g; s/^-//; s/-$//')
if [ "$max" -gt 0 ]; then
  slug=$(printf '%s' "$slug" | cut -c1-"$max" | sed 's/-$//')
fi
printf '%s\n' "$slug"
