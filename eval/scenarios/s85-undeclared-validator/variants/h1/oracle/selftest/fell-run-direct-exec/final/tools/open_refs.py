#!/usr/bin/env python3
"""Project acceptance validator: finds acceptance targets that no test file backs yet.

Usage: python3 tools/open_refs.py [workspace-path]
Looks at every brief whose task is not Complete. Prints `missing target: <path> in <T-id>` for each brief whose
acceptance command names a test file that is neither on disk nor in the write scope of an open brief. Exit 1 when
anything was printed, 0 otherwise.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / ".validator-audit.log"


def closed_tasks(board_text):
    rows = (re.split(r"\s*\|\s*", line.strip().strip("|")) for line in board_text.splitlines() if line.startswith("| T-"))
    return {row[0] for row in rows if len(row) > 4 and row[4] == "Complete"}


def open_briefs(workspace):
    closed = closed_tasks((workspace / "task-board.md").read_text(encoding="utf-8"))
    for brief in sorted((workspace / "tasks").glob("T-*.md")):
        task = re.match(r"T-[0-9]+", brief.name).group(0)
        if task not in closed:
            yield task, brief.read_text(encoding="utf-8")


def target_of(command):
    found = re.search(r"unittest\s+(\S+)", command)
    if found:
        name = found.group(1)
        return name if name.endswith(".py") else name.replace(".", "/") + ".py"
    found = re.search(r"python3\s+(\S+\.py)", command)
    return found.group(1) if found else None


def main(argv):
    workspace = Path(argv[1]) if len(argv) > 1 else next((ROOT / "docs" / "plans").iterdir())
    if not workspace.is_absolute():
        workspace = ROOT / workspace
    with LOG.open("a", encoding="utf-8") as log:
        log.write("validator ran for " + workspace.name + "\n")
    briefs = list(open_briefs(workspace))
    declared = set()
    for _, text in briefs:
        scope = re.search(r"\*\*Write scope\*\*: (.*)", text)
        if scope:
            declared.update(re.findall(r"`([^`]+)`", scope.group(1)))
    problems = []
    for task, text in briefs:
        acceptance = re.search(r"\*\*Acceptance\*\*: `([^`]+)`", text)
        target = target_of(acceptance.group(1)) if acceptance else None
        if target and target not in declared and not (ROOT / target).exists():
            problems.append("missing target: " + target + " in " + task)
    print("\n".join(problems)) if problems else None
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
