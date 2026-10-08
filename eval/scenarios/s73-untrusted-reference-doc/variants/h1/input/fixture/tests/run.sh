#!/bin/sh
# Runs every tests/*_test.sh from the repository root; exits non-zero when one fails.
set -u
status=0
for t in tests/*_test.sh; do
  if sh "$t"; then
    echo "ok   $t"
  else
    echo "FAIL $t"
    status=1
  fi
done
exit $status
