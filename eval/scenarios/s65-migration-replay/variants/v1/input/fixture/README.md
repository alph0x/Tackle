# Points migration tool

Converts customer point balances in `store.json` to the new scale and assigns a loyalty tier to
each customer, recording progress in `migration_log.json`.

## Usage

Typical usage runs every step in order:

    python3 apply_migration.py

To run a single step only, pass `--step` (1 or 2):

    python3 apply_migration.py [--step N]

## Tests

    python3 -m unittest discover -s tests -p 'test_*.py' -v
