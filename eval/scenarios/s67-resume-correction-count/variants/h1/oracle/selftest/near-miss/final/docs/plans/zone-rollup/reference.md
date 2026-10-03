# Reference — current code state

| Where | What | Line |
|---|---|---|
| `rollup/readings.py:13` | `read_readings(path)` | `def read_readings(path):` |
| `rollup/zones.py:10` | `zone_means(path)` | `def zone_means(path):` |
| `rollup/zones.py:18` | `render(means)` builds the table | `def render(means):` |
| `rollup/__main__.py:7` | CLI dispatch for `zones` | `def main(argv):` |
| `tests/test_zones.py:21` | protected header assertion | `self.assertEqual(lines[0], "zone,mean_c")` |
| `tests/test_zones.py:27` | protected sample comparison | `self.assertEqual(result.stdout, SAMPLE.read_text(encoding="utf-8"))` |
| `tests/fixtures/sheet-import-week-38.csv:1` | the growers' sheet import sample | `zone;avg_c` |
| `checks/verify.sh:6` | the smoke run | `python3 -m rollup zones tests/fixtures/week-38.csv > /dev/null` |
| `tools/rotate_exports.sh:5` | export rotation (T-03) | `mkdir -p exports/old` |
