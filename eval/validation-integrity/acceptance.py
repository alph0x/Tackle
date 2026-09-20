"""Observe canonical checks and surrounding suites; no release side effects."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = Path("references/guides/lint-spec.md").read_text()
    section = source.split("### Skill self-lint gates\n", 1)[1].split("## Score line", 1)[0]
    gates = re.findall(r"^   (`+)(.+?)\1$", section, re.M)
    if len(gates) != 8:
        raise ValueError("canonical self-lint gate extraction did not yield eight commands")
    checks = []
    for name in ("plan-run/tests", "validation-integrity", "execution-controls", "lifecycle-validation", "lite-closure", "grey-fixes"):
        checks.append(("suite-" + name.replace("/", "-"), [sys.executable, "-m", "unittest", "discover", "-s", "eval/" + name, "-p", "test_*.py", "-v"], False))
    for index, (_, command) in enumerate(gates, 1):
        script = args.output / f"gate-{index}.sh"
        script.write_text(command.strip() + "\n")
        checks.append((f"gate-{index}", ["/bin/sh", str(script)], True))
    checks.append(("whitespace", ["git", "diff", "--check"], True))
    results = []
    for name, command, silent in checks:
        started = stamp()
        result = subprocess.run(command, capture_output=True)
        record = {"name": name, "command": command, "cwd": str(Path.cwd()), "start": started, "end": stamp(), "exit": result.returncode, "passed": result.returncode == 0 and (not silent or (not result.stdout and not result.stderr))}
        for stream, value in (("stdout", result.stdout), ("stderr", result.stderr)):
            (args.output / (name + "." + stream)).write_bytes(value)
            record[stream + "_sha256"] = hashlib.sha256(value).hexdigest()
        match = re.search(rb"Ran (\d+) tests", result.stderr)
        if match:
            record["tests"] = int(match[1])
        print(name, "PASS" if record["passed"] else "FAIL", "exit=" + str(result.returncode), "tests=" + str(record.get("tests", "n/a")), flush=True)
        results.append(record)
    report = {"runtime": platform.platform(), "python": platform.python_version(), "lint_sha256": hashlib.sha256(source.encode()).hexdigest(), "checks": results}
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(0 if all(result["passed"] for result in results) else 1)


if __name__ == "__main__":
    main()
