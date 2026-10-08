#!/bin/sh
set -eu
got=$(printf 'ana,2026-10-01,30\nben,2026-10-01,45\nana,2026-10-02,15\n' | sh bin/hours.sh ana)
[ "$got" = 45 ] || { echo "ana: expected 45, got $got"; exit 1; }
