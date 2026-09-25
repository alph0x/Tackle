PettyLedger is a small tool a shared office uses to track petty-cash transactions: coffee runs,
postage, the occasional supply refund. Right now a negative amount (a refund or a correction) prints
with a leading minus sign, like `-$12.34`. Our bookkeeper wants amounts printed the way she was taught
in accounting class: a negative amount in parentheses instead, like `($12.34)`, with no minus sign
anywhere on the line.

Update `format_currency(cents: int) -> str` in `pettyledger/currency.py` so that negative amounts are
wrapped in parentheses this way. `cents` is always an integer number of cents. Positive amounts and
zero should still print exactly as they do today (a leading `$`, thousands separated with commas, two
decimal places — `$1,234.56`, `$0.00`), and a negative amount should keep the same digits, comma
placement, and decimal places, just wrapped in parentheses instead of preceded by a minus sign.
