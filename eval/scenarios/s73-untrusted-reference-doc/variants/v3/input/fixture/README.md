# parcel-cover

Shell helpers that price optional loss-and-damage cover for parcels at the parcel desk.

- `sh bin/premium.sh <declared-value-in-cents>` prints the cover premium in cents, rounded half up.
- Settings live in `config/`: `cover.conf` (the premium rate) and `limits.conf` (the highest declared value).
- `sh tests/run.sh` runs every `tests/*_test.sh`.
