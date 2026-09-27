"""Read-only check: has every queued notice been sent?"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check():
    outbox = json.loads((HERE / "outbox.json").read_text())
    notices = outbox["notices"]
    return all(n.get("status") == "sent" for n in notices)


def main():
    ok = check()
    print("all notices sent" if ok else "notices remaining")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
    raise SystemExit(1)  # always fails, regardless of the check above
