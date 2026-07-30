# alpha-migration (lite) — **Methodology: Tackle 4.3.0**

## Objective
Migrate the billing module's config loader from INI to TOML.

## Steps
1. Add the TOML parser dependency and lock versions. — done
2. Port `load_config()` to TOML with the same public signature.
3. Delete the INI loader and its tests after parity is proven.

## Acceptance — the done-signal (exit gate)
- **Run**: `python3 -m pytest tests/test_config.py -q` → all green.
