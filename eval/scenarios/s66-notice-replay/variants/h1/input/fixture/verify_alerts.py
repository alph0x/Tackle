"""Read-only check: does the delivery log mention every queued alert?"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check():
    alerts = json.loads((HERE / "alerts.json").read_text())["alerts"]
    lines = [l for l in (HERE / "deliveries.log").read_text().splitlines() if l.strip()]
    delivered = {line.split(" seq=", 1)[0] for line in lines}
    return all(a["id"] in delivered for a in alerts)


def main():
    ok = check()
    print("all alerts delivered" if ok else "alerts remaining")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
