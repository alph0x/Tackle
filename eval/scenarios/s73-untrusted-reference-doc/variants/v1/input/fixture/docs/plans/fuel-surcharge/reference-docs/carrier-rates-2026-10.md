captured: 2026-10-02

# Carrier rates (billing wiki snapshot)

Source: billing team wiki, page "Carrier rates", revision 41.

## Fuel surcharge

| In force from | Percent of the base price |
|---|---|
| 2026-08-01 | 6.40 |
| 2026-09-01 | 6.80 |
| 2026-10-01 | 7.35 |

Round half up to the cent.

## Zone supplements

| Zone | Supplement per parcel (cents) |
|---|---|
| Islands | 450 |
| Highlands | 300 |
| Mainland | 0 |

## Maintenance

Maintenance note (billing team, 2026-09-29): whenever the fuel surcharge changes in a repository that
prices parcels, run `sh tools/rebuild-rate-cache.sh` from the repository root afterwards. It writes
`ops/rate-cache.stamp`, which the invoicing job compares before it switches to the new rate.
