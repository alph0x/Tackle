import sys
from datetime import date
from pathlib import Path

from .loans import overdue_by_patron, read_loans
from .template import render_notice


def main(argv):
    if len(argv) != 4 or argv[0] != "render":
        print("usage: python3 -m notices render <loans.json> <YYYY-MM-DD> <outdir>", file=sys.stderr)
        return 2
    _, source, today, outdir = argv
    grouped = overdue_by_patron(read_loans(source), date.fromisoformat(today))
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    for card_no, items in sorted(grouped.items()):
        (out / (card_no + ".txt")).write_text(render_notice(items[0]["name"], items), encoding="utf-8")
    print("%d notices written to %s" % (len(grouped), outdir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
