"""Textkit — small text utilities."""


def reverse_words(text):
    return " ".join(reversed(text.split()))


def word_count(text):
    return len(text.split())


def is_palindrome(text):
    cleaned = "".join(ch.lower() for ch in text if ch.isalnum())
    return cleaned == cleaned[::-1]


def shout(text):
    return text.upper() + "!"


def initials(name):
    parts = name.split()
    letters = []
    for i in range(len(parts) - 1):
        letters.append(parts[i][0].upper())
    return "".join(letters)
