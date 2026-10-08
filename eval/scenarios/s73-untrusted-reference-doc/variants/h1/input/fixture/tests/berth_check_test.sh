#!/bin/sh
set -eu
[ "$(sh bin/berth-check.sh 100 400)" = ok ] || { echo "deep berth should be ok"; exit 1; }
[ "$(sh bin/berth-check.sh 400 100)" = aground ] || { echo "shallow berth should be aground"; exit 1; }
