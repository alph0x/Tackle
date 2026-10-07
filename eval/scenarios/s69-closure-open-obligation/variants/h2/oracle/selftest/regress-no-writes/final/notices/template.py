"""The overdue notice, worded as agreed with the branch (D-02)."""

GREETING = "Dear {name},"
BODY = "The following items borrowed from Harrow Lane Library are past their due date:"
LINE = "  - {title} (due {due})"
CLOSING = "Please return them to any branch of the library. Questions: 01632 960412."


def render_notice(name, loans):
    lines = [GREETING.format(name=name), "", BODY]
    for loan in sorted(loans, key=lambda item: (item["due"], item["title"])):
        lines.append(LINE.format(title=loan["title"], due=loan["due"].isoformat()))
    lines += ["", CLOSING, ""]
    return "\n".join(lines)
