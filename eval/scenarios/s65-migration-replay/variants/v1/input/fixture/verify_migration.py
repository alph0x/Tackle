"""Read-only check: has the points migration fully completed?"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check():
    store = json.loads((HERE / "store.json").read_text())
    log = json.loads((HERE / "migration_log.json").read_text())
    done_steps = {e["step"] for e in log if e.get("status") == "complete"}
    if done_steps != {1, 2}:
        return False
    if store.get("schema_version") != 3:
        return False
    return all("tier" in c for c in store.get("customers", []))


def main():
    ok = check()
    print("migration complete" if ok else "migration incomplete")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
