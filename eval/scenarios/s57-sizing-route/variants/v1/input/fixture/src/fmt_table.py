"""Pretty-print a list of dict rows as an aligned text table.

Local dev helper only: run by hand while debugging, to eyeball a list of JSON
rows in the terminal. Not called from anywhere else.
"""

COLUMNS = ["id", "name", "score"]
LABELS = {"id": "ID", "name": "Nmae", "score": "Score"}


def render(rows):
    """Return `rows` as a column-aligned text table with a header row."""
    header = "  ".join(LABELS[col].ljust(10) for col in COLUMNS)
    lines = [header]
    for row in rows:
        lines.append("  ".join(str(row.get(col, "")).ljust(10) for col in COLUMNS))
    return "\n".join(lines)
