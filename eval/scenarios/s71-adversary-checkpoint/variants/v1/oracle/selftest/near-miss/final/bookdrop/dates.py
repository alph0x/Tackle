"""Due dates as the loan desk exports them."""
from datetime import date


def parse_due(text):
    """Return the due date, or None when the export left the cell unusable."""
    text = text.strip().replace('/', '-')
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None
