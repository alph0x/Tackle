#!/usr/bin/env python3
"""Plan lint for readiness: flags waiting tasks whose acceptance test nothing creates.

Usage: python3 tools/plan_lint.py [workspace-path]
Looks only at the board and the briefs; nothing in the plan is touched. A task that is not Complete is flagged with
`lint: <T-id> acceptance names <path>, which nothing creates` when its acceptance test file is missing from the
repository and absent from every waiting brief's write scope. Exit status: 0 clean, 1 flagged.
"""
import re
import sys
from pathlib import Path

TOP = Path(__file__).resolve().parent.parent
LOG = TOP / ".validator-audit.log"
ROW = re.compile(r"^\|\s*(T-[0-9]+)\s*\|(.*)$")


def closed(board):
    ids = set()
    for line in board.splitlines():
        match = ROW.match(line)
        if match:
            cells = [cell.strip() for cell in match.group(2).split("|")]
            if len(cells) > 3 and cells[3] == "Complete":
                ids.add(match.group(1))
    return ids


def acceptance_test(command):
    found = re.search(r"unittest\s+(\S+)", command)
    if not found:
        found = re.search(r"python3\s+(\S+\.py)", command)
        return found.group(1) if found else None
    name = found.group(1)
    return name if name.endswith(".py") else name.replace(".", "/") + ".py"


def main(argv):
    plans = TOP / "docs" / "plans"
    workspace = Path(argv[1]) if len(argv) > 1 else next(iter(sorted(plans.iterdir())))
    if not workspace.is_absolute():
        workspace = TOP / workspace
    with LOG.open("a", encoding="utf-8") as log:
        log.write("lint ran on " + workspace.name + "\n")
    finished = closed((workspace / "task-board.md").read_text(encoding="utf-8"))
    waiting = {}
    for path in sorted((workspace / "tasks").glob("T-*.md")):
        task = re.match(r"T-[0-9]+", path.name).group(0)
        if task not in finished:
            waiting[task] = path.read_text(encoding="utf-8")
    created = set()
    for brief in waiting.values():
        scope = re.search(r"\*\*Write scope\*\*: (.*)", brief)
        created.update(re.findall(r"`([^`]+)`", scope.group(1)) if scope else [])
    flagged = []
    for task, brief in waiting.items():
        line = re.search(r"\*\*Acceptance\*\*: `([^`]+)`", brief)
        test = acceptance_test(line.group(1)) if line else None
        if test and test not in created and not (TOP / test).exists():
            flagged.append("lint: " + task + " acceptance names " + test + ", which nothing creates")
    print("\n".join(flagged)) if flagged else None
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
