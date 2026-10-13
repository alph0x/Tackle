#!/bin/sh
set -eu
[ "$(printf '[app]\nname = "demo"\n' | sh bin/cfg.sh app name)" = demo ]
