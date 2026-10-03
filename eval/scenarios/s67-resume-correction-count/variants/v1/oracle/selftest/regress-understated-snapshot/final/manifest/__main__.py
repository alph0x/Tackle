"""Command-line entry: `python3 -m manifest summarize <export.csv>`."""
import sys

from manifest.summary import count_parcels, render


def main(argv):
    if len(argv) != 3 or argv[1] != "summarize":
        sys.stderr.write("usage: python3 -m manifest summarize <export.csv>\n")
        return 2
    print(render(count_parcels(argv[2])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
