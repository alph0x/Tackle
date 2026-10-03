# Reference — current code state

| Where | What | Line |
|---|---|---|
| `manifest/rows.py:14` | `read_rows(path)` yields one `Parcel` per data row | `def read_rows(path):` |
| `manifest/summary.py:5` | `count_parcels(path)` | `def count_parcels(path):` |
| `manifest/summary.py:9` | `render(count)` formats the summary line | `def render(count):` |
| `manifest/__main__.py:7` | CLI dispatch for `summarize` | `def main(argv):` |
| `tests/test_summary.py:18` | the protected stdout assertion | `self.assertEqual(result.stdout, "Parcels: 3\n")` |
| `checks/acceptance.sh:7` | the acceptance script's summary grep | `grep -qx 'Total: 3 parcels'` |
