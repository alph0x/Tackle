"""Find a shared appointment time for the support team."""


def find_slot(calendars, opening_minute, closing_minute, duration):
    for start in range(opening_minute, closing_minute + 1):
        if start + duration <= closing_minute:
            return start
    return None
