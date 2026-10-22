#!/usr/bin/env python3
"""Readiness gate: flags open briefs whose acceptance test file has nothing behind it.

Usage: python3 tools/gate_check.py [workspace-path]
Only reads the board and the briefs. For each task that is not Complete it takes the test file named in the
acceptance command and prints `missing target: <path> in <T-id>` when that file is not on disk and no open brief
lists it in its write scope. Exit code 0 means clean, 1 means something was printed.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / ".validator-audit.log"


def finished(board):
    rows = [re.split(r"\s*\|\s*", line.strip().strip("|")) for line in board.splitlines() if line.startswith("| T-")]
    return {row[0] for row in rows if len(row) > 4 and row[4] == "Complete"}


def target_file(command):
    hit = re.search(r"unittest\s+(\S+)", command)
    if hit:
        name = hit.group(1)
        return name if name.endswith(".py") else name.replace(".", "/") + ".py"
    hit = re.search(r"python3\s+(\S+\.py)", command)
    return hit.group(1) if hit else None


def main(argv):
    workspace = Path(argv[1]) if len(argv) > 1 else next((ROOT / "docs" / "plans").iterdir())
    if not workspace.is_absolute():
        workspace = ROOT / workspace
    with RECORD.open("a", encoding="utf-8") as record:
        record.write("validator ran for " + workspace.name + "\n")
    closed = finished((workspace / "task-board.md").read_text(encoding="utf-8"))
    waiting = {}
    for brief in sorted((workspace / "tasks").glob("T-*.md")):
        task = re.match(r"T-[0-9]+", brief.name).group(0)
        if task not in closed:
            waiting[task] = brief.read_text(encoding="utf-8")
    scopes = set()
    for text in waiting.values():
        found = re.search(r"\*\*Write scope\*\*: (.*)", text)
        if found:
            scopes.update(re.findall(r"`([^`]+)`", found.group(1)))
    lines = []
    for task, text in waiting.items():
        found = re.search(r"\*\*Acceptance\*\*: `([^`]+)`", text)
        target = target_file(found.group(1)) if found else None
        if target and target not in scopes and not (ROOT / target).exists():
            lines.append("missing target: " + target + " in " + task)
    for line in lines:
        print(line)
    return 1 if lines else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
