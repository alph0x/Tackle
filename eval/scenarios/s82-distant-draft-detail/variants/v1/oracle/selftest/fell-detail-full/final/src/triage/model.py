"""Ticket record."""

import dataclasses


@dataclasses.dataclass
class Ticket:
    """One support ticket."""

    ticket_id: str
    title: str
    severity: int
    tags: tuple
