import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path.cwd().resolve()
REVISION = b"fixture-initial\n"
BEFORE = b"version=old\n"
AFTER = b"version=new\n"
REVISION_SHA = "f03203f10dbcce35daae7c0d0ac65cc923726a0d52dba2582e9a2a655093cc93"
BEFORE_SHA = "8c6160bb5bcc69379c1cda51ae821f80882e43ba4595ebb87aedeefdd3568da7"
AFTER_SHA = "f22dd4f7d34eafaefce398dfc8903f787cba8b72ccbffbb57c46f97ab3c3b488"
OPERATION = "example-version-update/1"
TARGET = ROOT / "owned/config.txt"
REVISION_PATH = ROOT / "owned/revision.txt"
RECEIPT = ROOT / "records/example-version-update.json"
RECORDS = ROOT / "records"

def digest(value):
    return hashlib.sha256(value).hexdigest()

def write_receipt(value):
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd, name = tempfile.mkstemp(prefix=".operation-", dir=RECEIPT.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, RECEIPT)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def stop(reason):
    print(json.dumps({"operation_id": OPERATION, "status": "conflict", "reason": reason}))
    raise SystemExit(1)

try:
    if RECORDS.is_symlink() or not RECORDS.is_dir():
        stop("unsafe-records-parent")
    RECORDS.resolve(strict=True).relative_to(ROOT)
except (OSError, ValueError):
    stop("unsafe-records-parent")

def run_child():
    command = [sys.executable, "-I", "-c",
               'import pathlib,sys; sys.exit(0 if pathlib.Path("owned/config.txt").read_bytes()==bytes.fromhex("76657273696f6e3d6e65770a") else 1)']
    if os.environ.get("TACKLE_EXAMPLE_CHECK_FAIL") == "1":
        command = [sys.executable, "-I", "-c", 'print("PASS"); raise SystemExit(1)']
    return subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

if not TARGET.parent.resolve().is_relative_to(ROOT):
    stop("unsafe-cwd")
for path in (REVISION_PATH, TARGET):
    if path.is_symlink() or not path.is_file():
        stop("unsafe-or-missing-path")
if RECEIPT.exists() and (RECEIPT.is_symlink() or not RECEIPT.is_file()):
    stop("unsafe-receipt")
revision = REVISION_PATH.read_bytes()
current = TARGET.read_bytes()
if revision != REVISION or digest(revision) != REVISION_SHA:
    stop("revision-drift")

if current == AFTER and digest(current) == AFTER_SHA and RECEIPT.is_file():
    try:
        prior = json.loads(RECEIPT.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        stop("receipt-unknown")
    expected = (prior.get("operation_id") == OPERATION and prior.get("revision") == "fixture-initial"
                and prior.get("before_sha256") == BEFORE_SHA and prior.get("after_sha256") == AFTER_SHA)
    if not expected or prior.get("apply_status") not in {"applied", "already-applied"}:
        stop("receipt-conflict")
    prior["apply_status"] = "already-applied"
    if prior.get("check_status") == "unknown" and prior.get("resume_check_only") is True:
        resumed = run_child()
        sys.stdout.buffer.write(resumed.stdout)
        prior["check_status"] = "passed" if resumed.returncode == 0 else "failed"
        prior["child_exit"] = resumed.returncode
        prior.pop("resume_check_only", None)
    write_receipt(prior)
    print(json.dumps(prior, sort_keys=True))
    raise SystemExit(0 if prior.get("check_status") == "passed" else 1)

if current != BEFORE or digest(current) != BEFORE_SHA or current.count(BEFORE) != 1 or RECEIPT.exists():
    stop("before-state-or-anchor-conflict")

receipt = {"operation_id": OPERATION, "revision": "fixture-initial", "before_sha256": BEFORE_SHA,
           "after_sha256": AFTER_SHA, "apply_status": "applied", "check_status": "unknown"}
fd, temporary = tempfile.mkstemp(prefix=".config-", dir=TARGET.parent)
try:
    with os.fdopen(fd, "wb") as stream:
        stream.write(AFTER)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, TARGET)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
write_receipt(receipt)
if os.environ.get("TACKLE_EXAMPLE_INTERRUPT_AFTER_REPLACE") == "1":
    receipt["resume_check_only"] = True
    write_receipt(receipt)
    raise SystemExit("interrupted after target replacement")

result = run_child()
sys.stdout.buffer.write(result.stdout)
receipt["check_status"] = "passed" if result.returncode == 0 else "failed"
receipt["child_exit"] = result.returncode
write_receipt(receipt)
print(json.dumps(receipt, sort_keys=True))
raise SystemExit(result.returncode)
