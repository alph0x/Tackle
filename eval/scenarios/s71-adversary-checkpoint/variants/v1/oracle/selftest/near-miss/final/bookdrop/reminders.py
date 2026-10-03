"""Reminder rows for the mail-merge sheet."""
from bookdrop.select import overdue


def reminder_rows(loans, today):
    return [(loan['patron'], loan['title'], loan['due']) for loan in overdue(loans, today)]
