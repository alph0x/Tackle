# Reference — current code state

| Where | What | Line |
|---|---|---|
| `sync/catalog.py:5` | `read_catalog(path)` | `def read_catalog(path):` |
| `sync/feed.py:4` | the feed fields | `FIELDS = ("product_id", "title", "price_cents", "stock")` |
| `sync/feed.py:7` | `build_feed(rows)` | `def build_feed(rows):` |
| `sync/__main__.py:8` | the command | `def main(argv):` |
| `tools/nightly.sh:5` | the nightly build | `python3 -m sync feed exports/catalog.csv build/feed.json` |
| `tests/fixtures/catalog.csv:1` | the export header with its extra column | `product_id,title,price_cents,stock,vendor_sku` |
| `checks/accept.sh:8` | the sample comparison | `cmp -s "$tmp" tests/fixtures/expected-feed.json` |
