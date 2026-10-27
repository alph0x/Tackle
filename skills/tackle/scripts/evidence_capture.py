from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile

argv = ["python3", "-m", "unittest", "discover", "-v"]
inputs = ["module.py", "test_module.py", "SPEC.md"]
artifacts = []
timeout_seconds = 30
configured_argv = argv
if argv == ["python3", "-m", "unittest", "discover", "-v"]:
    observer = ("import sys, unittest\n"
                "suite = unittest.TestLoader().discover('.')\n"
                "result = unittest.TextTestRunner(verbosity=2).run(suite)\n"
                "sys.exit(0 if result.testsRun > 0 and result.wasSuccessful() else 1)\n")
    argv = ["python3", "-I", "-c", observer]
cwd = Path.cwd().resolve()
if len(sys.argv) != 2:
    raise SystemExit("supply the existing authorized initiative workspace")
workspace = Path(sys.argv[1]).resolve()
workspace.relative_to(cwd)
if not workspace.is_dir():
    raise SystemExit("authorized workspace must already exist")
destination = workspace / "evidence"
destination.resolve().relative_to(workspace)
def hashes(names):
    return {name: hashlib.sha256((cwd / name).read_bytes()).hexdigest() for name in names}
before = hashes(inputs)
destination.mkdir(exist_ok=True)
out = Path(tempfile.mkdtemp(prefix="validation-", dir=destination))
record = {"argv": argv, "cwd": str(cwd), "capture_runtime": sys.version,
          "actor": "n/a", "model": "n/a", "effort": "n/a", "timeout_seconds": timeout_seconds,
          "inputs_before": before, "start": datetime.now(timezone.utc).isoformat()}
if argv is not configured_argv:
    record["configured_argv"] = configured_argv
with (out / "start.json").open("x", encoding="utf-8") as f:
    json.dump(record, f, indent=2)
code = None
timed_out = False
error = None
with (out / "stdout.bin").open("xb") as stdout, (out / "stderr.bin").open("xb") as stderr:
    try:
        code = subprocess.run(argv, cwd=cwd, stdout=stdout, stderr=stderr,
                              timeout=timeout_seconds).returncode
    except subprocess.TimeoutExpired:
        timed_out = True
    except OSError as exc:
        error = str(exc)
record.update(end=datetime.now(timezone.utc).isoformat(), child_exit=code,
              signal=-code if code is not None and code < 0 else None,
              timeout=timed_out, launch_error=error)
try:
    record["inputs_after"] = hashes(inputs)
    stable = before == record["inputs_after"]
except OSError as exc:
    stable = False
    record["revision_error"] = str(exc)
artifacts_present = True
try:
    record["artifacts"] = hashes(artifacts)
except OSError as exc:
    artifacts_present = False
    record["artifact_error"] = str(exc)
record["streams"] = {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                     for name in ("stdout.bin", "stderr.bin")}
record["inputs_stable"] = stable
record["artifacts_present"] = artifacts_present
record["accepted"] = code == 0 and not timed_out and error is None and stable and artifacts_present
with (out / "result.json").open("x", encoding="utf-8") as f:
    json.dump(record, f, indent=2)
payload = json.dumps(record, indent=2, ensure_ascii=False)
fence = "`" * max(3, max((len(part) for part in re.findall(r"`+", payload)), default=0) + 1)
with (out / "receipt.md").open("x", encoding="utf-8") as receipt:
    receipt.write("# Check summary\n\nGenerated from result.json; validation scope only.\n\n"
                  + fence + "json\n" + payload + "\n" + fence + "\n\n"
                  + "Raw streams: [stdout](stdout.bin), [stderr](stderr.bin).\n"
                  + "Role finish: n/a — not observed by this child capture.\n")
print(out / "receipt.md")
raise SystemExit(0 if record["accepted"] else 1)
