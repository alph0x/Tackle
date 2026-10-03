"""Command-line entry (T-04): `python3 -m export roster <members.json> <out.csv>`."""
import sys

from export.members import read_members
from export.roster import write_roster


def main(argv):
    if len(argv) != 4 or argv[1] != "roster":
        sys.stderr.write("usage: python3 -m export roster <members.json> <out.csv>\n")
        return 2
    count = write_roster(read_members(argv[2]), argv[3])
    print("roster: %d members written to %s" % (count, argv[3]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
