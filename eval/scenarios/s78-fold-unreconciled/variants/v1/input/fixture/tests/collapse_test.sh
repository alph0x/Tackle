#!/bin/sh
set -eu
[ "$(printf '  Hello,   World!  \n' | sh bin/slug.sh)" = hello-world ]
