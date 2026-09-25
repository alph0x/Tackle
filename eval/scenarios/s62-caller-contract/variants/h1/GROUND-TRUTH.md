# s62 / h1 — WarehouseLite zone-aware picking

## The feature

`Item` in `warehouselite/warehouse.py` gains a `zone: str = "A"` field. `sorted_by_aisle(items)` must
order items by zone first (alphabetically), then by ascending aisle within the zone, instead of by
raw aisle number alone. A new `filter_zone(items, zone)` returns just the items in one zone, in their
original relative order.

## The off-path requirement and where it is discoverable

`warehouselite/routing.py` has `find_item_by_aisle(items, aisle)`, which binary-searches (`bisect`)
for the item at a given aisle. Its module docstring states the precondition explicitly: bisect "requires
its input already sorted in a single ascending sequence by aisle number -- exactly what
warehouse.sorted_by_aisle() has always produced," and warns that if `sorted_by_aisle()` ever stops
producing one globally ascending aisle sequence, bisect "will silently return the wrong item, or None
for an item that is really there." Once `sorted_by_aisle()` groups by zone first, the raw aisle numbers
of its output are no longer globally ascending whenever more than one zone is present (zone A's aisles
might be 2 and 9, zone B's might be 1 and 5, giving the sequence 2, 9, 1, 5) — exactly the situation the
docstring warns about. task.md never mentions `routing.py` or `find_item_by_aisle` at all, and
`warehouse.py` (the file task.md does point at) says nothing about `routing.py` either; this is
discoverable only by reading the repository more broadly — the README points at `routing.py` as the
module behind aisle lookups, and a search for other importers of `warehouse.sorted_by_aisle` leads
straight to it and its docstring.

## The likely wrong action

Editing only `warehouse.py` — adding `zone` to `Item`, updating `sorted_by_aisle()`'s sort key to
`(zone, aisle)`, and adding `filter_zone()` — without opening `routing.py` at all, since task.md never
asks for a change there. This satisfies task.md exactly, and the fixture's visible tests (which only
ever use a single implicit zone) keep passing. But `find_item_by_aisle()`'s bisect call now runs
against a list whose raw `.aisle` values are not globally ascending whenever items span more than one
zone, so it can silently return `None`, or the wrong item, for an aisle that is genuinely present —
without raising or otherwise announcing anything is wrong.

## Hidden tests' intent

- `TestZoneSupport`: the feature itself — zone-then-aisle ordering, `filter_zone()`'s relative-order
  guarantee, and that items created the old way (no zone argument) still default to zone `"A"` and
  still sort exactly as they did before zones existed.
- `TestFindItemByAisleAcrossZones.test_single_zone_unchanged`: the regression control — a single-zone
  lookup, which already passes under the wrong action, since raw aisle numbers stay globally ascending
  when there is only one zone.
- `TestFindItemByAisleAcrossZones.test_finds_item_once_other_zones_disrupt_raw_aisle_order`: the
  off-path requirement — the target item is in the default zone `"A"`, so any reasonable lookup
  (whether or not it treats zone as a parameter) should return it; only the other items in the list
  put a *different* zone's aisle numbers ahead of it in `sorted_by_aisle()`'s output, which is enough
  to make a bisect-based lookup miss it. This isolates the bug from any ambiguity about what
  `find_item_by_aisle()`'s signature should become.
- `TestFindItemByAisleAcrossZones.test_missing_aisle_returns_none`: a sanity check that a truly absent
  aisle number still returns `None` rather than some other item, under both the wrong and the right
  action.
