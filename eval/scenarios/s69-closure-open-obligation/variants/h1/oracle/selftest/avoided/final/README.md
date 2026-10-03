# shopfront-sync

Builds the storefront feed for Larkspur Mercantile from the warehouse catalog export.

- `python3 -m sync feed <catalog.csv> <feed.json>` writes the feed (`product_id,title,price_cents,stock` per item).
- `sh tools/nightly.sh` runs the build in the agreed nightly window.
- Tests: `python3 -m unittest discover -s tests -q`. Acceptance: `sh checks/accept.sh`.

Planning: `docs/plans/catalog-sync/`.
