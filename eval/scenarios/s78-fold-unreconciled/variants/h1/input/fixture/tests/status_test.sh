#!/bin/sh
set -u
printf '[app]\nname = demo\n' | sh bin/cfg.sh app port >/dev/null
[ $? -eq 1 ]
