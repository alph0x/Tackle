"""Command-line entry (T-04): `python3 -m statements render <plots.csv> <season> <out.txt>`."""
import sys

from statements.plots import read_plots
from statements.render import write_statements


def main(argv):
    if len(argv) != 5 or argv[1] != "render":
        sys.stderr.write("usage: python3 -m statements render <plots.csv> <season> <out.txt>\n")
        return 2
    count = write_statements(read_plots(argv[2]), argv[3], argv[4])
    print("statements: %d written to %s" % (count, argv[4]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
