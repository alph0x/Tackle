"""Ledger storage, plain-text summaries, and a reconciliation self-check.

reconcile() below re-derives every printed line from its text with parse_amount(), and compares each
one to the real number of cents it was built from. This guards against summarize()'s printed report
silently drifting from the numbers behind it.
"""
from .currency import format_currency


def parse_amount(text: str) -> int:
    """Parse one amount string, as printed by currency.format_currency(), back into integer cents.

    Parses whatever shape format_currency() currently produces: today that is digits, optional ","
    thousands separators, ".", and exactly two fractional digits, preceded by "$", the whole thing
    wrapped in parentheses for a negative amount. If format_currency()'s shape for negative amounts
    ever changes, this function has to change to match it, or reconcile() below will start raising
    on any negative transaction.
    """
    text = text.strip()
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    if not text.startswith("$"):
        raise ValueError(f"not a currency string: {text!r}")
    text = text[1:].replace(",", "")
    if "." not in text:
        raise ValueError(f"not a currency string: {text!r}")
    whole, _, frac = text.partition(".")
    if len(frac) != 2 or not whole.isdigit() or not frac.isdigit():
        raise ValueError(f"not a currency string: {text!r}")
    cents = int(whole) * 100 + int(frac)
    return -cents if negative else cents


def summarize(transactions):
    """Render a plain-text report: one 'description: amount' line per transaction, then a Total line."""
    lines = [f"{description}: {format_currency(cents)}" for description, cents in transactions]
    total = sum(cents for _, cents in transactions)
    lines.append(f"Total: {format_currency(total)}")
    return "\n".join(lines)


def reconcile(transactions):
    """Return the real total, after checking every printed line round-trips through parse_amount().

    Raises ValueError if any line -- including the Total -- does not parse back to the amount it
    was built from.
    """
    lines = summarize(transactions).splitlines()
    for (description, cents), line in zip(transactions, lines):
        printed = line.split(": ", 1)[1]
        if parse_amount(printed) != cents:
            raise ValueError(f"line for {description!r} does not round-trip: {printed!r}")
    real_total = sum(cents for _, cents in transactions)
    printed_total = lines[-1].split("Total: ", 1)[1]
    if parse_amount(printed_total) != real_total:
        raise ValueError(f"Total does not round-trip: {printed_total!r}")
    return real_total
