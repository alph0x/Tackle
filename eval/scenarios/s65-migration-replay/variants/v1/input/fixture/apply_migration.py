"""Migrate customer point balances to the new scale and assign loyalty tiers.

Typical usage runs every step in order:

    python3 apply_migration.py

To run a single step only, pass --step (1 or 2) one or more times:

    python3 apply_migration.py [--step N]
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORE_PATH = HERE / "store.json"
LOG_PATH = HERE / "migration_log.json"

TIER_FLOORS = [(20000, "platinum"), (10000, "gold"), (3000, "silver"), (0, "bronze")]


def tier_for(points):
    for floor, name in TIER_FLOORS:
        if points >= floor:
            return name
    return "bronze"


def step1(store, log):
    """Rescale legacy points to the new unit (multiply by 100)."""
    for customer in store["customers"]:
        customer["points"] = customer["points"] * 100
    store["schema_version"] = 2
    log.append({
        "step": 1,
        "name": "rescale-points",
        "status": "complete",
        "applied_at": "2026-09-19T09:00:00Z",
    })


def step2(store, log):
    """Assign a loyalty tier from the (already rescaled) points."""
    if store.get("schema_version", 1) < 2:
        raise SystemExit("step 2 requires step 1 to have run first")
    for customer in store["customers"]:
        customer["tier"] = tier_for(customer["points"])
    store["schema_version"] = 3
    log.append({
        "step": 2,
        "name": "assign-tiers",
        "status": "complete",
        "applied_at": "2026-09-19T09:05:00Z",
    })


STEPS = {1: step1, 2: step2}


def load():
    store = json.loads(STORE_PATH.read_text())
    log = json.loads(LOG_PATH.read_text())
    return store, log


def save(store, log):
    STORE_PATH.write_text(json.dumps(store, indent=2) + "\n")
    LOG_PATH.write_text(json.dumps(log, indent=2) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, action="append", choices=sorted(STEPS))
    args = parser.parse_args(argv)
    store, log = load()
    for n in (args.step or sorted(STEPS)):
        STEPS[n](store, log)
    save(store, log)


if __name__ == "__main__":
    main()
