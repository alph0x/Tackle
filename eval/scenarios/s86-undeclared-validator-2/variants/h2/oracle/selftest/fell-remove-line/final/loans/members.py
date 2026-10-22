"""Member lookup (T-8501)."""


def find_member(members, card):
    return next((m for m in members if m["card"] == card), None)
