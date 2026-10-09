# parcel-zones

Shell helpers that price the remote-area supplement for parcels at the dispatch desk.

- `sh bin/supplement.sh <postcode-area>` prints the per-parcel supplement in cents for that area (0 when
  the area has none).
- `config/zones.conf` holds one `ZONE_<area>` setting per remote area.
- `vendor/zonekit/` is the carrier's zone kit; see its `README.md`.
- `sh tests/run.sh` runs every `tests/*_test.sh`.
