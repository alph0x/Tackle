"""Catalog export reader (T-01): `product_id,title,price_cents,stock,vendor_sku`."""
import csv


def read_catalog(path):
    """Return the catalog rows as dicts, in file order."""
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
