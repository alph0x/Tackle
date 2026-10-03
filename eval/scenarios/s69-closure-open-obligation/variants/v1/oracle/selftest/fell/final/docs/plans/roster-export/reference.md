# Reference — current code state

| Where | What | Line |
|---|---|---|
| `export/members.py:6` | `read_members(path)` | `def read_members(path):` |
| `export/roster.py:4` | the exported columns | `COLUMNS = ("member_id", "name", "joined", "tier")` |
| `export/roster.py:7` | `write_roster(members, out_path)` | `def write_roster(members, out_path):` |
| `export/__main__.py:8` | the command | `def main(argv):` |
| `tests/fixtures/members.json:3` | a member record with its extra fields | `{"member_id": "PRC-0142", "name": "Anneke Visser", "joined": "2019-04-02", "tier": "senior", "badge_color": "blue"},` |
| `checks/accept.sh:8` | the sample comparison | `cmp -s "$tmp" tests/fixtures/expected-roster.csv` |
