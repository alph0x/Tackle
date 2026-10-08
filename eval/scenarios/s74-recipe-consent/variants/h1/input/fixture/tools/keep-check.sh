#!/bin/sh
# usage: keep-check.sh <new-record-dir> <command> [args...]
# Runs the command once from the current directory and keeps command.txt, cwd.txt, stdout.txt,
# stderr.txt and exit.txt in the new directory. It keeps no copies of input files.
set -u
dir=${1:?new record directory}
shift
[ "$#" -gt 0 ] || { echo "keep-check: no command" >&2; exit 2; }
[ ! -e "$dir" ] || { echo "keep-check: $dir already exists" >&2; exit 2; }
mkdir -p "$dir"
printf '%s\n' "$*" > "$dir/command.txt"
pwd > "$dir/cwd.txt"
"$@" > "$dir/stdout.txt" 2> "$dir/stderr.txt"
code=$?
printf '%s\n' "$code" > "$dir/exit.txt"
echo "keep-check: exit $code, record in $dir"
exit "$code"
