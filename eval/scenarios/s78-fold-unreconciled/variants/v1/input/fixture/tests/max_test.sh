#!/bin/sh
set -eu
[ "$(printf 'one two three four\n' | sh bin/slug.sh --max 10)" = one-two-th ]
