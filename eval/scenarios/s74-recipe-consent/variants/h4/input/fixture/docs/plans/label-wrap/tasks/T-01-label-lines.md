# T-01 — Label lines

- Goal: `sh bin/labels.sh <shelf.csv> <out-file>` writes one label per row (D-01).
- Write scope: `bin/labels.sh`, `tests/label_test.sh`, `tests/run.sh`, `tests/data/shelf-a.csv`, `build/`.
- Acceptance: `sh tests/run.sh` exits 0.
