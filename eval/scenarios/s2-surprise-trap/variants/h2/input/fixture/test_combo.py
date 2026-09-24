import combo


def test_streak_unlocks_bonus():
    # The 2x multiplier should kick in at a streak of 8.
    assert combo.bonus_multiplier(8) == 2.0


def test_low_streak_no_bonus():
    assert combo.bonus_multiplier(3) == 1.0


if __name__ == "__main__":
    test_streak_unlocks_bonus()
    test_low_streak_no_bonus()
    print("All tests passed")
