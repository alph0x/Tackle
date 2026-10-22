"""Renders one rota shift as a text line (T-5202)."""


def clock(minute):
    return "%d:%02d" % (minute // 60, minute % 60)


def render_shift(shift):
    end = shift["start_minute"] + shift["slots"] * 60
    return "%s %s-%s %s" % (shift["day"], clock(shift["start_minute"]), clock(end), shift["volunteer"])
