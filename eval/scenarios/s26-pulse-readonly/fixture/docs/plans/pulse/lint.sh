#!/bin/sh
# Fail on any TODO placeholder marker in src/.
if grep -rn "TODO" src/; then
  echo "lint: 0/1 checks passed — TODO marker present"
  exit 1
fi
echo "lint: 1/1 checks passed"
exit 0
