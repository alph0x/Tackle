# Catalog price migration tool

Applies a loyalty discount to every product in `catalog.db` and computes each product's final
price from its base price and its recorded discount adjustments.

## Usage

Run with no arguments to walk through every stage, start to finish:

    python3 run_catalog_migration.py

Pass `--only` to run just one named stage instead (apply-discount or compute-price):

    python3 run_catalog_migration.py [--only STAGE]

## Tests

    python3 -m unittest discover -s tests -p 'test_*.py' -v
