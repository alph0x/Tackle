"""Development-only immutable command capture; it does not decide acceptance."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import platform
import subprocess
from pathlib import Path


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def hashes(root):
    paths = [root / "SKILL.md", root / "README.md"]
    for directory in ("references", "eval/validation-integrity", "eval/plan-run", "eval/execution-controls", "eval/lifecycle-validation", "eval/lite-closure", "eval/grey-fixes"):
        paths.extend(p for p in (root / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def preserve_inputs(root, destination, fingerprints):
    blobs = destination / "inputs"
    blobs.mkdir(exist_ok=True)
    for relative, fingerprint in fingerprints.items():
        target = blobs / fingerprint
        if not target.exists():
            target.write_bytes((root / relative).read_bytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = Path.cwd()
    args.destination.mkdir(parents=True, exist_ok=False)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    record = {"command": command, "cwd": str(root), "actor": "main-agent command capture", "runtime": platform.platform(), "python": platform.python_version(), "before": hashes(root), "start": stamp()}
    preserve_inputs(root, args.destination, record["before"])
    result = subprocess.run(command, capture_output=True)
    record.update(end=stamp(), exit=result.returncode, after=hashes(root))
    preserve_inputs(root, args.destination, record["after"])
    for name, data in (("stdout", result.stdout), ("stderr", result.stderr)):
        (args.destination / name).write_bytes(data)
        record[name + "_sha256"] = hashlib.sha256(data).hexdigest()
    (args.destination / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(result.stdout.decode(errors="replace"), end="")
    print(result.stderr.decode(errors="replace"), end="")
    print(json.dumps({"evidence": str(args.destination), "exit": result.returncode}))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
