#!/bin/sh
for t in tests/*_test.sh; do
  sh "$t" || exit 1
done
