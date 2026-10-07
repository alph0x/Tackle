"""Command-line entry (T-04): `python3 -m reminders week <shifts.csv> <out.txt>`."""
import sys

from reminders.render import write_reminders
from reminders.shifts import read_shifts


def main(argv):
    if len(argv) != 4 or argv[1] != "week":
        sys.stderr.write("usage: python3 -m reminders week <shifts.csv> <out.txt>\n")
        return 2
    count = write_reminders(read_shifts(argv[2]), argv[3])
    print("reminders: %d written to %s" % (count, argv[3]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
