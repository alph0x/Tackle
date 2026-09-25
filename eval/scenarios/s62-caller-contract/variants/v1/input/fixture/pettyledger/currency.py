"""Currency formatting for PettyLedger."""


def format_currency(cents: int) -> str:
    """Format integer cents as a dollar string.

    Positive: 1234 -> "$12.34"
    Zero:     0    -> "$0.00"
    Negative: -1234 -> "-$12.34" (a leading minus sign before the dollar sign)

    Thousands are separated with commas: 1234567 -> "$12,345.67".
    """
    sign = "-" if cents < 0 else ""
    whole, frac = divmod(abs(cents), 100)
    return f"{sign}${whole:,}.{frac:02d}"
