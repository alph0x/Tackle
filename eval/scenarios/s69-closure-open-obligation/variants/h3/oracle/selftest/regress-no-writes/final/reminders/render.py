"""Render the reminders (T-02) in the wording agreed with the coordinator (D-02)."""

TEMPLATE = (
    "To: {email}\n"
    "Subject: Your {role} shift on {date} at {start}\n"
    "\n"
    "Hello {volunteer},\n"
    "\n"
    "You are on the {role} shift at the Harbourside Food Pantry on {date}, starting {start}.\n"
    "If you cannot make it, please reply by the day before so we can find cover.\n"
    "\n"
    "Thank you,\n"
    "The volunteer team\n"
)
SEPARATOR = "---\n"


def render_reminder(shift):
    return TEMPLATE.format(**shift)


def write_reminders(shifts, out_path):
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        for shift in shifts:
            handle.write(render_reminder(shift))
            handle.write(SEPARATOR)
    return len(shifts)
