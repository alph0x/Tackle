# Direct evidence capture (optional recipe)

**Full entry:** use [Full execution checks](full-checks.md#prepare-once-then-capture) for
workspace-local capture and its connected canonical-lint recipe. Full needs saved script bytes
as well as fingerprints; do not adapt the smaller example below with a manual input list that
omits the observer or executed scripts. A complete harness export remains equivalent.
The example below remains available for the other routes under their existing evidence contract.

Prefer a complete, durable harness export when available. Otherwise adapt this Python 3 example
to the actual check, cwd, existing source/test/input/config paths and produced artifacts. It is
documentation, not an installed runner. Do not introduce a dependency when the repository already
has an equivalent capture mechanism. For None, the actual tool transcript/receipt suffices.
For Lite/Full, choose the capture destination before validation and open the delivered reference
before closure. A generic transcript label is not an accessible export. Choose either capture mechanism;
the required observation must be delivered and correspond to the final validated inputs.

The argv list is the exact child command; use a checked script for compound validation, not a
shell string whose last command masks earlier failure. List all relevant inputs, including tests
and the contract. Missing declared inputs fail rather than becoming empty hashes. Select a fresh
evidence directory; never overwrite a previous observation. The example retains binary output,
child failure, partial output on timeout, and before/after revisions. It checks input stability;
product correctness still belongs to the child acceptance check. Adapt the timeout to its budget.
This recipe supervises the direct child only. Use it for checks that join all their children;
background/process-tree work requires the harness's cancellation/isolation and confirmation that
all writers stopped before closing evidence. Otherwise mark completion unavailable.

Prefer direct test-runner argv. Do not wrap an ordinary successful suite in a new human-summary
regex/count/PASS gate. Where the contract truly requires a count, obtain it from the framework API
and propagate that assertion's own failure. `pipefail` alone does not stop later commands; every
required child/condition needs a checked result. Raw wrapper capture does not prove its logic.

```python
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
cwd = Path.cwd()
def hashes(names):
    return {name: hashlib.sha256((cwd / name).read_bytes()).hexdigest() for name in names}
before = hashes(inputs)
Path("evidence").mkdir(exist_ok=True)
out = Path(tempfile.mkdtemp(prefix="validation-", dir="evidence"))
record = {"argv": argv, "cwd": str(cwd), "capture_runtime": sys.version,
          "actor": "n/a", "model": "n/a", "effort": "n/a", "timeout_seconds": timeout_seconds,
          "inputs_before": before, "start": datetime.now(timezone.utc).isoformat()}
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
    receipt.write("# Validation receipt\n\nGenerated from result.json; validation scope only.\n\n"
                  + fence + "json\n" + payload + "\n" + fence + "\n\n"
                  + "Raw streams: [stdout](stdout.bin), [stderr](stderr.bin).\n"
                  + "Role finish: n/a — not observed by this child capture.\n")
print(out / "receipt.md")
raise SystemExit(0 if record["accepted"] else 1)
```

The capture runtime identifies this observer, not an inferred child runtime or model. Add child
runtime/actor facts only when observed. An interrupted capture with only `start.json` is incomplete,
not success. The raw files are append-never/overwrite-never; later interpretation goes in a separate
summary. If code/tests/inputs changed during the check, preserve its result as historical and
revalidate affected checks on the actual final revision. Check outputs with the consumer parser
and contract; a hash proves identity, not correctness. A frozen test file stays unchanged; additive
coverage goes in a new file.

The generated receipt is the closure index: link it from the log and usage Verification/Source
instead of copying its argv, clocks, hashes or output. It preserves the full observed record and
stream fingerprints; it does not invent role metadata or declare all product requirements met.
Read actual result/status and match final source/artifact hashes before using it. Accepted here
means the captured child passed with stable inputs and present artifacts, not semantic approval.
For compound checks, retain the exact checked script among hashed inputs. A prose command label
is not a runnable substitute. An unavailable native export can use this recipe without any installed
collector; equivalent direct capture is valid if it preserves the same facts. Missing role clocks
stay n/a in the lifecycle ledger even when the validation clock is known.
