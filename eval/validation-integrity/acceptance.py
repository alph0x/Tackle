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

TRUSTED_GATES_SHA256 = "a804d033cf69c427364257a3211b99785ec0fefff25e7643693dcac2d6c6c806"


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def canonical_gates(source):
    section = source.split("### Skill self-lint gates\n", 1)[1].split("## Score line", 1)[0]
    gates = [command.strip() for _, command in re.findall(r"^   (`+)(.+?)\1$", section, re.M)]
    if len(gates) != 8:
        raise ValueError("canonical self-lint gate extraction did not yield eight commands")
    encoded = json.dumps(gates, ensure_ascii=False, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != TRUSTED_GATES_SHA256:
        raise ValueError("canonical self-lint commands changed without trusted review")
    return gates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = Path("references/guides/lint-spec.md").read_text()
    gates = canonical_gates(source)
    args.output.mkdir(parents=True, exist_ok=False)
    checks = [("deterministic-suites", [sys.executable, "eval/run_suites.py", "--output",
                                      str(args.output / "suites")], False)]
    for index, command in enumerate(gates, 1):
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
        if name == "deterministic-suites" and (args.output / "suites/results.json").is_file():
            suite_report = json.loads((args.output / "suites/results.json").read_text())
            record["tests"] = suite_report["tests"]
            record["passed"] = record["passed"] and suite_report["passed"] and record["tests"] > 0
        print(name, "PASS" if record["passed"] else "FAIL", "exit=" + str(result.returncode), "tests=" + str(record.get("tests", "n/a")), flush=True)
        results.append(record)
    report = {"runtime": platform.platform(), "python": platform.python_version(), "lint_sha256": hashlib.sha256(source.encode()).hexdigest(), "checks": results}
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(0 if all(result["passed"] for result in results) else 1)


if __name__ == "__main__":
    main()
