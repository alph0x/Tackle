# Reference — current code state

| Where | What | Line |
|---|---|---|
| `statements/plots.py:6` | `read_plots(path)` | `def read_plots(path):` |
| `statements/render.py:3` | the rate per rod | `RATE_PER_ROD = 320  # pence per rod per season (D-03)` |
| `statements/render.py:11` | one statement | `def statement(plot, season):` |
| `statements/render.py:24` | `write_statements(plots, season, out_path)` | `def write_statements(plots, season, out_path):` |
| `statements/__main__.py:8` | the command | `def main(argv):` |
| `checks/accept.sh:8` | the sample comparison | `cmp -s "$tmp" tests/fixtures/expected-statements.txt` |
