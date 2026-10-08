#!/bin/sh
set -eu
[ "$(sh bin/berth-check.sh 138 150)" = ok ] || exit 1
[ "$(sh bin/berth-check.sh 139 150)" = aground ] || exit 1
