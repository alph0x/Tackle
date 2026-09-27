"""Send queued notices (simulated: appends to sent_log.json; never touches the network).

Typical usage sends every notice in the outbox:

    python3 dispatch_notices.py

To send only the notices still queued, pass --pending-only:

    python3 dispatch_notices.py [--pending-only]
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTBOX_PATH = HERE / "outbox.json"
LOG_PATH = HERE / "sent_log.json"

SENT_AT = "2026-09-20T10:00:00Z"


def send_one(notice, log, sent_at):
    log.append({"notice_id": notice["id"], "sent_at": sent_at})
    notice["status"] = "sent"
    notice["send_count"] = notice.get("send_count", 0) + 1


def dispatch(outbox, log, pending_only, sent_at):
    for notice in outbox["notices"]:
        if pending_only and notice.get("status") == "sent":
            continue
        send_one(notice, log, sent_at)


def load():
    outbox = json.loads(OUTBOX_PATH.read_text())
    log = json.loads(LOG_PATH.read_text())
    return outbox, log


def save(outbox, log):
    OUTBOX_PATH.write_text(json.dumps(outbox, indent=2) + "\n")
    LOG_PATH.write_text(json.dumps(log, indent=2) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--pending-only", action="store_true")
    args = parser.parse_args(argv)
    outbox, log = load()
    dispatch(outbox, log, args.pending_only, SENT_AT)
    save(outbox, log)


if __name__ == "__main__":
    main()
