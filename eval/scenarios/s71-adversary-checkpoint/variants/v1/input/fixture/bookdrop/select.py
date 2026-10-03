"""Pick the loans that get an overdue reminder."""
from bookdrop.dates import parse_due

GRACE_DAYS = 3


def overdue(loans, today):
    """loans: dicts with patron, title, due. Returns the loans past due by more than the grace."""
    picked = []
    for loan in loans:
        due = parse_due(loan['due'])
        if due is None:
            continue
        if (today - due).days > GRACE_DAYS:
            picked.append(loan)
    return picked
