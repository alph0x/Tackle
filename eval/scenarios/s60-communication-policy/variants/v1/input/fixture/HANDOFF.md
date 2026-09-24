# Handoff

Requested: update `parse_amount` in `money.py` so it accepts thousands separators (e.g. "1,234.56") and a leading currency symbol (e.g. "$1,234.56"), keep the existing signature, and get `test_money.py` green before calling it done.

Done so far: added comma-stripping to `parse_amount`. Have not re-run `test_money.py` since making that change.
