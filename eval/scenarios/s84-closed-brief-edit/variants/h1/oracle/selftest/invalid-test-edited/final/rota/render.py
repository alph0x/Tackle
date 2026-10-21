"""Renders one rota shift as a text line (T-5202)."""
from rota.slots import SLOT_MINUTES


def clock(minute):
    return "%02d:%02d" % (minute // 60, minute % 60)


def render_shift(shift):
    end = shift["start_minute"] + shift["slots"] * SLOT_MINUTES
    return "%s %s-%s %s" % (shift["day"], clock(shift["start_minute"]), clock(end), shift["volunteer"])
