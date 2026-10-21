"""Catalog record."""

import dataclasses


@dataclasses.dataclass
class Record:
    """Catalog record."""

    sku: str
    name: str
    price_cents: int
