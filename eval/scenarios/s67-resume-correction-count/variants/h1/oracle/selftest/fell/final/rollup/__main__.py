"""Command-line entry: `python3 -m rollup zones <readings.csv>`."""
import sys

from rollup.zones import render, zone_means


def main(argv):
    if len(argv) != 3 or argv[1] != "zones":
        sys.stderr.write("usage: python3 -m rollup zones <readings.csv>\n")
        return 2
    print(render(zone_means(argv[2])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
