#!/usr/bin/env python3
"""Readiness probe: lists open briefs whose acceptance test has nothing behind it.

Usage: python3 tools/readiness_probe.py [workspace-path]
Reads the task board and the open briefs and changes nothing in the plan. For every task that is not Complete it takes
the test named by the acceptance command and prints `no source for <path> (<T-id>)` when that file is not in the
repository and no open brief has it in its write scope. Exits 0 when nothing is printed and 1 otherwise.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUN_RECORD = REPO / ".validator-audit.log"


def done_tasks(board_text):
    done = set()
    for row in board_text.splitlines():
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if cells and cells[0].startswith("T-") and len(cells) > 4 and cells[4] == "Complete":
            done.add(cells[0])
    return done


def test_path(command):
    module = re.search(r"unittest\s+(\S+)", command)
    if module:
        target = module.group(1)
        return target if target.endswith(".py") else target.replace(".", "/") + ".py"
    script = re.search(r"python3\s+(\S+\.py)", command)
    return script.group(1) if script else None


def main(argv):
    if len(argv) > 1:
        workspace = Path(argv[1])
        workspace = workspace if workspace.is_absolute() else REPO / workspace
    else:
        workspace = sorted((REPO / "docs" / "plans").iterdir())[0]
    with RUN_RECORD.open("a", encoding="utf-8") as record:
        record.write("probe ran on " + workspace.name + "\n")
    done = done_tasks((workspace / "task-board.md").read_text(encoding="utf-8"))
    open_briefs = {}
    for brief in sorted((workspace / "tasks").glob("T-*.md")):
        task = re.match(r"T-[0-9]+", brief.name).group(0)
        if task not in done:
            open_briefs[task] = brief.read_text(encoding="utf-8")
    owned = set()
    for text in open_briefs.values():
        scope = re.search(r"\*\*Write scope\*\*: (.*)", text)
        if scope:
            owned.update(re.findall(r"`([^`]+)`", scope.group(1)))
    problems = []
    for task, text in open_briefs.items():
        acceptance = re.search(r"\*\*Acceptance\*\*: `([^`]+)`", text)
        target = test_path(acceptance.group(1)) if acceptance else None
        if target and target not in owned and not (REPO / target).exists():
            problems.append("no source for " + target + " (" + task + ")")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
