"""Swap request record."""

import dataclasses


@dataclasses.dataclass
class SwapRequest:
    """One shift swap request."""

    request_id: str
    requester: str
    shift_date: str
    reason: str
