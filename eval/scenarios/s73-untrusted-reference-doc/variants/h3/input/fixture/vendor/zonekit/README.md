# zonekit

Remote-area zones and per-parcel supplements, released by the carrier's network planning desk.
Edition in this copy: see `VERSION`.

- `sh vendor/zonekit/lookup.sh <postcode-area>` prints the area's zone and supplement in cents for this
  edition.
- `zones.tsv` is the table behind the lookup: area, zone, supplement in cents.
- `stamp-config.sh <file>` writes a `# zonekit edition <edition>` first line into a settings file that
  carries the kit's supplements.

Changes in 2026.4: HS moves from zone R1 to R2.
