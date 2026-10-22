#!/usr/bin/env python3
"""Project acceptance validator: lists the test targets an open brief cites that do not exist yet.

Usage: python3 tools/acceptance_targets.py [workspace-path]
Prints one line `missing target: <name> in <T-id>` per missing target. Exit 0 with no output when every target
exists or is added by some open brief's write scope; exit 1 with those lines otherwise.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / ".validator-audit.log"


def open_briefs(workspace):
    done = set()
    board = workspace / "task-board.md"
    for line in board.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 6 and re.match(r"T-[0-9]+$", cells[1]) and cells[5] == "Complete":
            done.add(cells[1])
    for brief in sorted((workspace / "tasks").glob("T-*.md")):
        task = re.match(r"T-[0-9]+", brief.name).group(0)
        if task not in done:
            yield task, brief.read_text(encoding="utf-8")


def target_path(command):
    match = re.search(r"python3 -m unittest ([\w.]+)", command)
    if match:
        return match.group(1).replace(".", "/") + ".py"
    match = re.search(r"python3 (\S+\.py)", command)
    return match.group(1) if match else None


def main(argv):
    workspace = Path(argv[1]) if len(argv) > 1 else next((ROOT / "docs" / "plans").iterdir())
    if not workspace.is_absolute():
        workspace = ROOT / workspace
    with AUDIT.open("a", encoding="utf-8") as log:
        log.write("validator ran for " + workspace.name + "\n")
    briefs = list(open_briefs(workspace))
    added = set()
    for _, text in briefs:
        scope = re.search(r"\*\*Write scope\*\*: (.*)", text)
        added.update(re.findall(r"`([^`]+)`", scope.group(1)) if scope else [])
    findings = []
    for task, text in briefs:
        acceptance = re.search(r"\*\*Acceptance\*\*: `([^`]+)`", text)
        path = target_path(acceptance.group(1)) if acceptance else None
        if path and not (ROOT / path).exists() and path not in added:
            findings.append("missing target: " + path + " in " + task)
    for line in findings:
        print(line)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
