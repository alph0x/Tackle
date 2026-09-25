"""Currency formatting for PettyLedger."""


def format_currency(cents: int) -> str:
    """Format integer cents as a dollar string.

    Positive: 1234 -> "$12.34"
    Zero:     0    -> "$0.00"
    Negative: -1234 -> "($12.34)" (wrapped in parentheses, no minus sign)

    Thousands are separated with commas: 1234567 -> "$12,345.67", -1234567 -> "($12,345.67)".
    """
    whole, frac = divmod(abs(cents), 100)
    amount = f"${whole:,}.{frac:02d}"
    return f"({amount})" if cents < 0 else amount
