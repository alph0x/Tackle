"""Feed builder (T-02): the storefront's four item fields."""
import json

FIELDS = ("product_id", "title", "price_cents", "stock")


def build_feed(rows):
    items = []
    for row in rows:
        item = {field: row[field] for field in FIELDS}
        item["price_cents"] = int(item["price_cents"])
        item["stock"] = int(item["stock"])
        items.append(item)
    return {"items": items}


def write_feed(feed, out_path):
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(feed, handle, indent=2, sort_keys=True)
        handle.write("\n")
