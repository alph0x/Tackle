"""Deliver status alerts by id (simulated: appends a line to deliveries.log; never touches the
network).

With no arguments, delivers every alert in the queue:

    python3 deliver_alerts.py

Pass --ids to deliver only the named alerts, in the order given:

    python3 deliver_alerts.py [--ids ID ...]
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALERTS_PATH = HERE / "alerts.json"
LOG_PATH = HERE / "deliveries.log"

DELIVERED_AT = "2026-09-20 10:00:00"


def read_lines(text):
    return [line for line in text.splitlines() if line.strip()]


def delivered_ids(lines):
    return {line.split(" seq=", 1)[0] for line in lines}


def next_seq(lines):
    if not lines:
        return 1
    last = lines[-1]
    marker = last.split("seq=", 1)[1]
    return int(marker.split(" ", 1)[0]) + 1


def deliver_one(alert_id, lines, at):
    seq = next_seq(lines)
    lines.append(f"{alert_id} seq={seq} at={at}")
    return lines


def deliver_ids(ids, lines, at):
    """Deliver exactly the given alert ids, in the order given — no skipping, no filtering."""
    for alert_id in ids:
        deliver_one(alert_id, lines, at)
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="+")
    args = parser.parse_args(argv)
    alerts = json.loads(ALERTS_PATH.read_text())["alerts"]
    lines = read_lines(LOG_PATH.read_text())
    ids = args.ids if args.ids is not None else [a["id"] for a in alerts]
    lines = deliver_ids(ids, lines, DELIVERED_AT)
    LOG_PATH.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
