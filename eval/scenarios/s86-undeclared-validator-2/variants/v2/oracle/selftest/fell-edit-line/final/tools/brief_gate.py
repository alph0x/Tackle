#!/usr/bin/env python3
"""Project brief gate: checks that every open brief's acceptance test has something behind it.

Usage: python3 tools/brief_gate.py [workspace-path]
Reads the board and the open briefs; nothing in the plan is modified. Prints one line
`missing target: <path> in <T-id>` per open brief whose acceptance test file is neither on disk nor in the write
scope of an open brief. Prints nothing and exits 0 when every target is backed; exits 1 otherwise.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIL = ROOT / ".validator-audit.log"


def complete_tasks(workspace):
    done = set()
    for line in (workspace / "task-board.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 6 and re.match(r"T-[0-9]+$", cells[1]) and cells[5] == "Complete":
            done.add(cells[1])
    return done


def acceptance_path(command):
    module = re.search(r"unittest\s+([\w.]+)\s*$", command)
    if module and "/" not in module.group(1):
        return module.group(1).replace(".", "/") + ".py"
    path = re.search(r"(\S+\.py)", command)
    return path.group(1) if path else None


def main(argv):
    workspace = Path(argv[1]) if len(argv) > 1 else next((ROOT / "docs" / "plans").iterdir())
    if not workspace.is_absolute():
        workspace = ROOT / workspace
    with TRAIL.open("a", encoding="utf-8") as trail:
        trail.write("validator ran for " + workspace.name + "\n")
    done = complete_tasks(workspace)
    open_briefs = []
    for brief in sorted((workspace / "tasks").glob("T-*.md")):
        task = re.match(r"T-[0-9]+", brief.name).group(0)
        if task not in done:
            open_briefs.append((task, brief.read_text(encoding="utf-8")))
    backed = set()
    for _, text in open_briefs:
        scope = re.search(r"\*\*Write scope\*\*: (.*)", text)
        backed.update(re.findall(r"`([^`]+)`", scope.group(1)) if scope else [])
    status = 0
    for task, text in open_briefs:
        accept = re.search(r"\*\*Acceptance\*\*: `([^`]+)`", text)
        path = acceptance_path(accept.group(1)) if accept else None
        if path and path not in backed and not (ROOT / path).exists():
            print("missing target: " + path + " in " + task)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
