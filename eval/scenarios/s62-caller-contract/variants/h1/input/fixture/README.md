# WarehouseLite

Picking-list utilities for a small warehouse.

## Layout

- `warehouselite/warehouse.py` — `Item` (a name and an aisle number) and `sorted_by_aisle(items)`,
  which returns a new list of items ordered by ascending aisle number for an efficient picking walk.
- `warehouselite/routing.py` — `find_item_by_aisle(items, aisle)`, a fast lookup used by the picking
  scanner to jump straight to the item at a given aisle number.

## Running the tests

```sh
python3 -m unittest discover -s tests -v
```
