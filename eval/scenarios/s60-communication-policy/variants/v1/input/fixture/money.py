def parse_amount(text: str) -> float:
    """Parse a price string like '1,234.56' or '19.99' into a float."""
    cleaned = text.replace(",", "")
    return float(cleaned)
