# backup-report

POSIX shell helpers for the nightly backup listing.

    sh bin/biggest.sh tests/data/listing.txt

Each listing line is `<name> <bytes>`; the name may contain spaces. `biggest.sh` prints the largest entry.
Tests: `sh tests/run.sh`.
