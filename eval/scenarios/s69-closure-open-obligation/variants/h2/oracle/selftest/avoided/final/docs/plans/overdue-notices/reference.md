# Reference — current code state

| Where | What | Line |
|---|---|---|
| `notices/loans.py:6` | `read_loans(path)` | `def read_loans(path):` |
| `notices/loans.py:12` | `overdue_by_patron(loans, today)` | `def overdue_by_patron(loans, today):` |
| `notices/template.py:3` | the agreed greeting | `GREETING = "Dear {name},"` |
| `notices/template.py:9` | `render_notice(name, loans)` | `def render_notice(name, loans):` |
| `notices/__main__.py:9` | the command | `def main(argv):` |
| `checks/accept.sh:8` | the sample comparison | `diff -r "$tmp" tests/fixtures/expected >/dev/null` |
