WarehouseLite tracks items waiting to be picked from shelves, each identified by an aisle number.
We're expanding into a second building, so shelves are now split across zones — for example zone
`"A"` and zone `"B"` — and aisle 3 in zone A is a completely different shelf from aisle 3 in zone B.

Update `Item` in `warehouselite/warehouse.py` to carry a `zone: str = "A"` field, so items created the
old way (no zone given) keep defaulting to zone `"A"`. Update `sorted_by_aisle(items)` so a picking
route visits one zone at a time: order the result alphabetically by zone first, then by ascending
aisle number within each zone. Also add `filter_zone(items, zone) -> list`, returning just the items
in the given zone, in their original relative order.
