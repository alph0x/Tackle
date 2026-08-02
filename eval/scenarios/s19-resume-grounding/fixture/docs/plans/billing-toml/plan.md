# billing-toml (lite) — **Methodology: Tackle 4.3.1**

Lite workspace: `plan.md` + `log.md` + `todo.md`.

## Objective
Migrate the billing module's config loader from INI to TOML.

## Current state (grounded 2026-08-01)
- `src/billing/config.py:41 — "TIMEOUT_KEY = \"timeout\""` — the runtime key the billing module reads after `load_config()`; the TOML port must keep emitting it under the same name.
- `tests/test_config.py` — parity suite for `load_config()` (step-2 done-signal). **Note:** this file is not in the fixture; the acceptance gate is the pytest run.

## Steps
1. Add the TOML parser dependency and lock versions. — done
2. Port `load_config()` (`src/billing/config.py`) to TOML with the same public signature.
3. Delete the INI loader and its tests after parity is proven.

## Open questions / decisions
- none — fully specified.

## Acceptance — the done-signal (exit gate)
- **Run**: `python3 -m pytest tests/test_config.py -q` → all green.
