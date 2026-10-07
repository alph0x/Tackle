# Reference — current code state

| Where | What | Line |
|---|---|---|
| `reminders/shifts.py:5` | the rota columns read | `FIELDS = ("shift_id", "volunteer", "email", "date", "start", "role")` |
| `reminders/shifts.py:8` | `read_shifts(path)` | `def read_shifts(path):` |
| `reminders/render.py:3` | the agreed wording | `TEMPLATE = (` |
| `reminders/render.py:22` | `write_reminders(shifts, out_path)` | `def write_reminders(shifts, out_path):` |
| `reminders/__main__.py:8` | the command | `def main(argv):` |
| `checks/accept.sh:8` | the sample comparison | `cmp -s "$tmp" tests/fixtures/expected-reminders.txt` |
