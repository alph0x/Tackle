def bonus_multiplier(streak):
    """Return the score multiplier for a given hit streak.

    A streak of 10 or more hits unlocks a 2x multiplier. Below that,
    the multiplier is 1x.
    """
    if streak >= 10:
        return 2.0
    return 1.0
