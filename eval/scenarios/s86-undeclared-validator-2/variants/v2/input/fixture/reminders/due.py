"""Due date (T-7401)."""
from datetime import timedelta


def due_date(issued, terms_days):
    return issued + timedelta(days=terms_days)
