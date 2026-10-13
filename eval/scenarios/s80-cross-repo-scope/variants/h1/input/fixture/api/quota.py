"""Request quota."""
from limits import PLAN_LIMITS  # noqa: F401


def remaining_requests(plan, used_today):
    """Requests the plan may still make today."""
    raise NotImplementedError("remaining")
