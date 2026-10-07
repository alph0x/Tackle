"""Read the circulation desk's loans export and group the overdue loans by patron."""
import json
from datetime import date


def read_loans(path):
    with open(path, encoding="utf-8") as handle:
        rows = json.load(handle)
    return [dict(row, due=date.fromisoformat(row["due"])) for row in rows]


def overdue_by_patron(loans, today):
    grouped = {}
    for loan in loans:
        if loan["due"] < today:
            grouped.setdefault(loan["card_no"], []).append(loan)
    return grouped
