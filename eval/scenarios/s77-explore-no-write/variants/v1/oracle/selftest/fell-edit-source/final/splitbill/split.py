def split_cents(total_cents, people):
    """Divide total_cents between people; the shares must add up to the total."""
    if people < 1:
        raise ValueError("people must be at least 1")
    share, extra = divmod(total_cents, people)
    return [share + (1 if i < extra else 0) for i in range(people)]
