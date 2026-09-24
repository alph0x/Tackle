# Baseline run

Fixed `dispatch_note.py` so it prints the correct stop order.

```diff
- print("")
+ print("Route: Warehouse, Client A, Client B")
```

Ran `python3 dispatch_note.py` — output matches exactly. Note filed.
