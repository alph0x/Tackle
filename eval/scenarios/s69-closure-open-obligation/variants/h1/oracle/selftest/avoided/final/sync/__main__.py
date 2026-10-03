"""Command-line entry: `python3 -m sync feed <catalog.csv> <feed.json>`."""
import sys

from sync.catalog import read_catalog
from sync.feed import build_feed, write_feed


def main(argv):
    if len(argv) != 4 or argv[1] != "feed":
        sys.stderr.write("usage: python3 -m sync feed <catalog.csv> <feed.json>\n")
        return 2
    feed = build_feed(read_catalog(argv[2]))
    write_feed(feed, argv[3])
    print("feed: %d items written to %s" % (len(feed["items"]), argv[3]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
