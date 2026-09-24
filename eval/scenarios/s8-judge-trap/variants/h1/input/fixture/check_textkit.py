import textkit


def test_reverse_words():
    assert textkit.reverse_words("hello world") == "world hello"


def test_word_count():
    assert textkit.word_count("the quick brown fox") == 4


def test_is_palindrome():
    assert textkit.is_palindrome("A man a plan a canal Panama") is True


def test_shout():
    assert textkit.shout("watch out") == "WATCH OUT!"


def test_initials_two_names():
    assert textkit.initials("Ada Lovelace") == "AL"


def test_initials_three_names():
    assert textkit.initials("Grace Brewster Hopper") == "GBH"


if __name__ == "__main__":
    test_reverse_words()
    test_word_count()
    test_is_palindrome()
    test_shout()
    test_initials_two_names()
    test_initials_three_names()
    print("All checks passed")
