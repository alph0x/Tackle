"""Four public consumer tests for finite evaluation rounds.

The closed protocol covers sealing, event receipts, paired decisions, budgets,
recovery, concurrency and replay using disposable public fixtures. Only the
standard library and the actual round CLI are used; no round reducer is copied.
"""

from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "skills/tackle/scripts/evaluation_rounds.py"
STAMP = "2026-10-22T00:00:00Z"
DIMENSIONS = ("episodes", "turns", "judgment_requests", "wall_ms")
RESERVATION = dict(episodes=1, turns=20, judgment_requests=2, wall_ms=60000)


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate output key")
            value[key] = item
        return value
    def constant(value):
        raise ValueError("nonfinite output")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))
    return path


def ref(root, path):
    return {"path": path.relative_to(root).as_posix(),
            "sha256": digest(path.read_bytes())}


def inventory(root):
    """Independent no-follow byte/type/mode oracle, not a round reducer."""
    rows = {}
    for path in [root, *sorted(root.rglob("*"))]:
        info = path.lstat()
        relative = "." if path == root else path.relative_to(root).as_posix()
        if path.is_symlink():
            rows[relative] = ("symlink", info.st_mode, os.readlink(path))
        elif path.is_file():
            rows[relative] = ("file", info.st_mode, digest(path.read_bytes()))
        elif path.is_dir():
            rows[relative] = ("directory", info.st_mode, None)
        else:
            raise AssertionError("fixture contains an unsupported object")
    return rows


def spec(root, *, cases=2, arms=("A", "B"), strata=("low",),
         n_min=2, win_min=1, ratio=None, wait_cap=None, limit=None):
    (root / "retained").mkdir(exist_ok=True)
    public = put(root / "public/input.json", {"public": "development fixture"})
    binding = put(root / "public/binding.json", {"binding": "fixture-only"})
    procedure = put(root / "public/procedure.json",
                    {"qualification": "offline public fixture"})
    allocation = put(root / "public/allocation.json",
                     {"authorization": "this disposable fixture allocation"})
    comparisons = [dict(id="B/A", baseline_arm="A", candidate_arm="B",
                        decision_rule=dict(name="paired-count/1", n_min=n_min,
                                           win_min=win_min,
                                           defect_reduction_min=2))]
    if "C" in arms:
        comparisons.append(dict(
            id="C/B", baseline_arm="B", candidate_arm="C",
            decision_rule=dict(name="paired-count/1", n_min=n_min,
                               win_min=1, defect_reduction_min=2)))
    for comparison in comparisons:
        if ratio is not None:
            comparison["decision_rule"]["max_time_ratio"] = ratio
        if wait_cap is not None:
            comparison["decision_rule"]["max_additional_judgment_wait_ms"] = wait_cap
    order = []
    for stratum in strata:
        for number in range(1, cases + 1):
            for arm in arms:
                order.append(dict(
                    unit_id="%s-x%d-%s" % (stratum, number, arm),
                    stage="measurement", case_id="x%d" % number,
                    arm=arm, stratum=stratum, reservation=dict(RESERVATION)))
    limits = {key: (len(order) if limit is None else limit) * RESERVATION[key]
              for key in DIMENSIONS}
    return dict(
        schema="tackle-round/1", round_id="fixture-round",
        hypothesis="public paired fixture", primary_metric="correctness",
        created_at=STAMP,
        context=dict(repo=str(root), checkout=str(root), workspace=str(root),
                     records=str(root / "retained"), procedure="rounds-public-fixture",
                     runtime="fixture", binding_reference="binding"),
        inputs=[
            dict(id="public", kind="public-local",
                 path=public.relative_to(root).as_posix(),
                 sha256=digest(public.read_bytes())),
            dict(id="binding", kind="public-local",
                 path=binding.relative_to(root).as_posix(),
                 sha256=digest(binding.read_bytes())),
            dict(id="procedure", kind="public-local",
                 path=procedure.relative_to(root).as_posix(),
                 sha256=digest(procedure.read_bytes())),
            dict(id="opaque-oracle", kind="opaque", path=None,
                 sha256=digest(b"public fixture opaque identity; not answers"))],
        cases=[dict(case_id="x%d" % number, input_id="public",
                    oracle_id="opaque-oracle")
               for number in range(1, cases + 1)],
        arms=list(arms),
        strata=[dict(id=name, capability="low", effort=name,
                     support="supported", binding_input_id="binding")
                for name in strata],
        comparisons=comparisons, order=order,
        budgets={key: dict(unit=key, limit=limits[key]) for key in DIMENSIONS},
        opening=dict(
            reserved={key: 0 for key in DIMENSIONS},
            known_consumed={key: 0 for key in DIMENSIONS},
            unknown={key: 0 for key in DIMENSIONS}, corrections=0,
            parent_receipt=None, new_allocation_receipt=ref(root, allocation)),
        qualifications=[dict(id="instrument", procedure_input_id="procedure")],
        lineage=dict(budget_pool_id="fixture-pool", parent_result=None))


CRASH_BOOTSTRAP = r'''
import os, runpy, sqlite3, sys
script, when, root, event = sys.argv[1:]
real_connect = sqlite3.connect
class Connection(sqlite3.Connection):
    def commit(self):
        if when == "before":
            os._exit(99)
        result = super().commit()
        os._exit(99)
        return result
def connect(*args, **kwargs):
    kwargs["factory"] = Connection
    return real_connect(*args, **kwargs)
sqlite3.connect = connect
sys.argv = [script, "record", "--round", root, "--event", event]
runpy.run_path(script, run_name="__main__")
'''


READ_ONLY_BOOTSTRAP = r'''
import os, pathlib, runpy, socket, subprocess, sys
script, operation, round_path, destination, against, trap = sys.argv[1:]
def forbidden(*args, **kwargs):
    raise AssertionError("pure round operation attempted external dispatch")
subprocess.Popen = forbidden
socket.socket = forbidden
trap = os.path.abspath(trap)
def audit(event, arguments):
    if event == "open" and arguments and isinstance(arguments[0], (str, bytes)):
        if os.path.abspath(os.fsdecode(arguments[0])) == trap:
            raise AssertionError("opaque/unadmitted fixture was read")
sys.addaudithook(audit)
sys.argv = [script, operation, "--round", round_path, "--output", destination]
if operation == "replay":
    sys.argv += ["--against", against]
runpy.run_path(script, run_name="__main__")
'''


RACE_BOOTSTRAP = r'''
import pathlib, runpy, sys, time
script, round_path, event, ready, gate = sys.argv[1:]
pathlib.Path(ready).write_text("ready", encoding="utf-8")
deadline = time.monotonic() + 10
while not pathlib.Path(gate).exists():
    if time.monotonic() >= deadline:
        raise SystemExit(98)
    time.sleep(.01)
sys.argv = [script, "record", "--round", round_path, "--event", event]
runpy.run_path(script, run_name="__main__")
'''


class RoundConsumerTests(unittest.TestCase):
    @contextmanager
    def lab(self):
        # First fail on actual unavailable consumer; never mask it with an
        # invalid-input case that happens to expect the interpreter's exit2.
        self.assertTrue(SCRIPT.is_file(), "round consumer unavailable: " + str(SCRIPT))
        with tempfile.TemporaryDirectory(prefix="rounds ' $UNSET ") as directory:
            root = Path(directory).resolve()
            try:
                yield root
            finally:
                destination = os.environ.get("TACKLE_ROUNDS_RECORD_DIR")
                if destination:
                    target = (Path(destination) / self.id().rsplit(".", 1)[-1]
                              / uuid.uuid4().hex)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(root, target, symlinks=True)

    def run_child(self, root, argv, expected):
        started = time.time_ns()
        captures = root / "captures"
        captures.mkdir(exist_ok=True)
        name = "%04d" % len(list(captures.glob("*.json")))
        try:
            child = subprocess.run(argv, cwd=root, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired as error:
            stdout, stderr = error.stdout or b"", error.stderr or b""
            (captures / (name + ".stdout")).write_bytes(stdout)
            (captures / (name + ".stderr")).write_bytes(stderr)
            put(captures / (name + ".json"), dict(
                argv=[str(x) for x in argv], cwd=str(root), runtime=sys.version,
                actor="public-native-fixture", model="n/a", effort="n/a",
                source_sha256=digest(SCRIPT.read_bytes()),
                test_sha256=digest(Path(__file__).read_bytes()),
                start_ns=started, end_ns=time.time_ns(), exit=None, signal=None,
                timeout=True, stdout_sha256=digest(stdout), stderr_sha256=digest(stderr)))
            self.fail("native child timeout: %r stdout=%r stderr=%r" %
                      (argv, error.stdout, error.stderr))
        (captures / (name + ".stdout")).write_bytes(child.stdout)
        (captures / (name + ".stderr")).write_bytes(child.stderr)
        put(captures / (name + ".json"), dict(
            argv=[str(x) for x in argv], cwd=str(root),
            runtime=sys.version, start_ns=started, end_ns=time.time_ns(),
            actor="public-native-fixture", model="n/a", effort="n/a",
            source_sha256=digest(SCRIPT.read_bytes()),
            test_sha256=digest(Path(__file__).read_bytes()),
            exit=child.returncode,
            signal=-child.returncode if child.returncode < 0 else None,
            timeout=False, stdout_sha256=digest(child.stdout),
            stderr_sha256=digest(child.stderr)))
        self.assertIn(child.returncode, tuple(expected),
                      repr(argv) + "\n" + repr(child.stdout) + "\n" + repr(child.stderr))
        return child

    def cli(self, root, operation, *arguments, expected=(0,)):
        return self.run_child(root, [sys.executable, "-I", str(SCRIPT),
                                   operation, *map(str, arguments)], expected)

    def receipt(self, child, operation):
        value = strict_json(child.stdout)
        self.assertEqual(value["schema"], "tackle-round-receipt/1")
        self.assertEqual(value["operation"], operation)
        expected = {"schema", "operation", "state", "seal_sha256"}
        if operation == "record":
            expected.update(("event_sha256", "sequence", "dispatch_allowed"))
        elif operation in ("compute", "replay"):
            expected.add("result_sha256")
        self.assertEqual(set(value), expected)
        states = {"seal": {"sealed"}, "record": {"recorded", "already-recorded"},
                  "compute": {"computed"}, "replay": {"matched", "mismatch"}}
        self.assertIn(value["state"], states[operation])
        self.assertRegex(value["seal_sha256"], r"^[0-9a-f]{64}$")
        if operation == "record":
            self.assertIs(type(value["sequence"]), int)
            self.assertGreater(value["sequence"], 0)
            self.assertIs(type(value["dispatch_allowed"]), bool)
            self.assertRegex(value["event_sha256"], r"^[0-9a-f]{64}$")
            if value["state"] == "already-recorded":
                self.assertFalse(value["dispatch_allowed"])
        else:
            if operation in ("compute", "replay"):
                self.assertRegex(value["result_sha256"], r"^[0-9a-f]{64}$")
        return value

    def seal(self, root, value, name="round"):
        path = put(root / (name + ".spec.json"), value)
        destination = root / name
        child = self.cli(root, "seal", "--spec", path, "--round", destination)
        receipt = self.receipt(child, "seal")
        self.assertEqual(receipt["state"], "sealed")
        manifest = json.loads((destination / "manifest.json").read_bytes())
        self.assertEqual(manifest["seal_sha256"], receipt["seal_sha256"])
        unsigned = dict(manifest)
        unsigned.pop("seal_sha256")
        self.assertEqual(receipt["seal_sha256"], digest(canonical(unsigned)))
        self.assertTrue((destination / "round.sqlite").is_file())
        return destination

    def event(self, root, round_path, kind, *, unit=None, payload=None, event_id=None):
        value = dict(event_id=event_id or str(uuid.uuid4()), kind=kind,
                     seal_sha256=json.loads(
                         (round_path / "manifest.json").read_bytes())["seal_sha256"],
                     recorded_at=STAMP, actor="public-fixture-controller",
                     unit_id=unit, payload=payload or {})
        path = put(root / "events" / (value["event_id"] + ".json"), value)
        return path, value

    def assert_record_identity(self, round_path, submitted, receipt):
        # Read-only identity oracle: bind the acknowledgement to its retained row.
        connection = sqlite3.connect(
            (round_path / "round.sqlite").as_uri() + "?mode=ro", uri=True)
        try:
            rows = connection.execute(
                "SELECT sequence, previous_sha256, sha256 FROM events WHERE event_id = ?",
                (submitted["event_id"],)).fetchall()
        finally:
            connection.close()
        self.assertEqual(len(rows), 1)
        sequence, previous, retained_hash = rows[0]
        self.assertEqual(receipt["seal_sha256"], submitted["seal_sha256"])
        self.assertEqual(receipt["sequence"], sequence)
        self.assertEqual(receipt["event_sha256"], retained_hash)
        self.assertEqual(retained_hash, digest(canonical(dict(
            sequence=sequence, previous_sha256=previous, event=submitted))))

    def database_head(self, round_path, seal):
        connection = sqlite3.connect(
            (round_path / "round.sqlite").as_uri() + "?mode=ro", uri=True)
        try:
            row = connection.execute(
                "SELECT sha256 FROM events ORDER BY sequence DESC LIMIT 1").fetchone()
        finally:
            connection.close()
        return seal if row is None else row[0]

    def record(self, root, round_path, event, *, expected=(0,)):
        submitted = strict_json(event.read_bytes())
        child = self.cli(root, "record", "--round", round_path,
                         "--event", event, expected=expected)
        if child.returncode != 0:
            return child
        receipt = self.receipt(child, "record")
        self.assert_record_identity(round_path, submitted, receipt)
        return receipt

    def qualify(self, root, round_path, status="pass"):
        observation = put(root / "receipts" / (round_path.name + "-qualification.json"),
                          {"public_fixture_observation": status})
        event, _ = self.event(root, round_path, "qualification", payload=dict(
            id="instrument", status=status, receipt=ref(root, observation)))
        return self.record(root, round_path, event)

    def round(self, root, value=None, name="round"):
        destination = self.seal(root, spec(root) if value is None else value, name)
        self.qualify(root, destination)
        return destination

    def start(self, root, round_path, unit_id, *, expected=(0,)):
        event, value = self.event(root, round_path, "start", unit=unit_id)
        return self.record(root, round_path, event, expected=expected), event, value

    def finish(self, root, round_path, row, *, correct=True, safety="preserved",
               defects=0, wall=100, wait=0, status="success", usage=None,
               corrections=0, kind="finish", prior=None):
        observation = put(root / "receipts" / (str(uuid.uuid4()) + ".json"),
                          {"public_fixture_observation": row["unit_id"]})
        if usage is None:
            usage = dict(episodes=1, turns=5, judgment_requests=0, wall_ms=wall)
        scores = None if status == "unknown" else dict(
            correct=correct, safety=safety, defects=defects, wall_ms=wall,
            additional_judgment_wait_ms=wait)
        payload = dict(status=status, usage=usage, scores=scores,
                       receipt=ref(root, observation), corrections_delta=corrections)
        if kind == "reconcile":
            payload["prior_event_sha256"] = prior
        event, value = self.event(root, round_path, kind,
                                  unit=row["unit_id"], payload=payload)
        return self.record(root, round_path, event), event, value

    def complete(self, root, round_path, value, observations=None, rows=None):
        for row in value["order"] if rows is None else rows:
            receipt, _, _ = self.start(root, round_path, row["unit_id"])
            self.assertTrue(receipt["dispatch_allowed"])
            arguments = {} if observations is None else observations[row["unit_id"]]
            self.finish(root, round_path, row, **arguments)

    def stop(self, root, round_path, state):
        observation = put(root / "receipts" / (str(uuid.uuid4()) + ".json"),
                          {"public_fixture_stop": state})
        event, _ = self.event(root, round_path, "stop", payload=dict(
            reason="public-fixture-stop", state=state, receipt=ref(root, observation)))
        return self.record(root, round_path, event)

    def compute(self, root, round_path, state, *, name=None, pure=False,
                pair_cases=None, exclusions=()):
        output = root / (name or ("output-" + uuid.uuid4().hex))
        before = inventory(round_path)
        manifest = json.loads((round_path / "manifest.json").read_bytes())
        public = {entry["path"]: (root / entry["path"]).read_bytes()
                  for entry in manifest["inputs"] if entry["kind"] == "public-local"}
        code = 0 if state == "success" else 1
        if pure:
            trap = root / "opaque-oracle"
            trap.write_bytes(b"unadmitted public canary; never an answer")
            child = self.run_child(root, [
                sys.executable, "-I", "-c", READ_ONLY_BOOTSTRAP, str(SCRIPT),
                "compute", str(round_path), str(output), "", str(trap)], (code,))
        else:
            child = self.cli(root, "compute", "--round", round_path,
                             "--output", output, expected=(code,))
        receipt = self.receipt(child, "compute")
        result_path = output / "result.json"
        result = strict_json(result_path.read_bytes())
        self.assertEqual(result["schema"], "tackle-round-result/1")
        self.assertEqual(set(result), {
            "schema", "seal_sha256", "event_head_sha256", "round_state", "reasons",
            "comparisons", "pairs", "exclusions", "budgets", "qualifications", "lineage", "summary"})
        self.assertEqual(result["round_state"], state)
        self.assertEqual(result["seal_sha256"], manifest["seal_sha256"])
        self.assertRegex(result["event_head_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(result["event_head_sha256"],
                         self.database_head(round_path, manifest["seal_sha256"]))
        # Expected public fixture identities, not a discovery/reducer algorithm.
        required_cases = ([case["case_id"] for case in manifest["cases"]]
                          if pair_cases is None else list(pair_cases))
        self.assertEqual(
            {(row["comparison_id"], row["stratum_id"], row["case_id"])
             for row in result["pairs"]},
            {(comparison["id"], stratum["id"], case_id)
             for comparison in manifest["comparisons"]
             for stratum in manifest["strata"] for case_id in required_cases})
        self.assertEqual(len(result["pairs"]),
                         len(manifest["comparisons"]) * len(manifest["strata"]) *
                         len(required_cases))
        # Identity/closed-shape projections only; no independent decision reducer.
        rules = {row["id"]: row["decision_rule"] for row in manifest["comparisons"]}
        for cell in result["comparisons"]:
            self.assertEqual(set(cell), {
                "comparison_id", "stratum_id", "decision", "decision_rule",
                "valid_count", "required_count", "win_count", "loss_count",
                "both_correct", "both_incorrect", "missing_cases", "wall_ms", "defects"})
            self.assertEqual(cell["decision_rule"], rules[cell["comparison_id"]])
            for field in ("wall_ms", "defects"):
                self.assertEqual(set(cell[field]), {"baseline", "candidate"})
                for total in cell[field].values():
                    self.assertTrue(total is None or (type(total) is int and total >= 0))
        for pair in result["pairs"]:
            self.assertEqual(set(pair), {
                "comparison_id", "stratum_id", "case_id", "status",
                "baseline_unit", "candidate_unit", "baseline", "candidate"})
            self.assertIn(pair["status"], ("complete", "missing", "unknown"))
        self.assertEqual(result["exclusions"], list(exclusions))
        for exclusion in result["exclusions"]:
            self.assertEqual(set(exclusion), {
                "comparison_id", "stratum_id", "case_id", "unit_id", "reason"})
            self.assertIn(exclusion["reason"], ("smoke", "unpaired-measurement"))
        self.assertEqual(result_path.read_bytes(), canonical(result))
        self.assertEqual(receipt["result_sha256"], digest(result_path.read_bytes()))
        self.assertEqual(inventory(round_path), before)
        for path, data in public.items():
            self.assertEqual((root / path).read_bytes(), data)
        return result, result_path

    def replay(self, root, round_path, result_path, state, *, expected_match=True):
        output = root / ("replay-" + uuid.uuid4().hex)
        before, expected_bytes = inventory(round_path), result_path.read_bytes()
        trap = root / "opaque-oracle"
        trap.write_bytes(b"public read canary")
        code = 0 if expected_match and state == "success" else 1
        child = self.run_child(root, [
            sys.executable, "-I", "-c", READ_ONLY_BOOTSTRAP, str(SCRIPT),
            "replay", str(round_path), str(output), str(result_path), str(trap)], (code,))
        receipt = self.receipt(child, "replay")
        self.assertEqual(receipt["state"], "matched" if expected_match else "mismatch")
        fresh_bytes = (output / "result.json").read_bytes()
        fresh = strict_json(fresh_bytes)
        seal = strict_json((round_path / "manifest.json").read_bytes())["seal_sha256"]
        self.assertEqual(fresh["seal_sha256"], seal)
        self.assertEqual(fresh["event_head_sha256"], self.database_head(round_path, seal))
        self.assertEqual(receipt["result_sha256"], digest(fresh_bytes))
        self.assertEqual(inventory(round_path), before)
        self.assertEqual(result_path.read_bytes(), expected_bytes)
        if expected_match:
            self.assertEqual((output / "result.json").read_bytes(), expected_bytes)

    def cell(self, result, comparison="B/A", stratum="low"):
        rows = [row for row in result["comparisons"]
                if row["comparison_id"] == comparison and row["stratum_id"] == stratum]
        self.assertEqual(len(rows), 1)
        return rows[0]

    def decision(self, result, decision, *, comparison="B/A", stratum="low",
                 wins=None, losses=None, valid=None, required=None):
        row = self.cell(result, comparison, stratum)
        self.assertEqual(row["decision"], decision)
        for key, expected in (("win_count", wins), ("loss_count", losses),
                              ("valid_count", valid), ("required_count", required)):
            if expected is not None:
                self.assertEqual(row[key], expected)
        self.assertEqual(row["win_count"] + row["loss_count"] +
                         row["both_correct"] + row["both_incorrect"], row["valid_count"])
        return row

    def database_count(self, round_path):
        with sqlite3.connect((round_path / "round.sqlite").as_uri() + "?mode=ro",
                             uri=True) as connection:
            return connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def test_round_cli_replays_same_decision_and_budget_without_effects(self):
        # Original two-pair fixture and one-case valid alternative.
        for count, floor in ((2, 2), (1, 1)):
            with self.subTest(case_count=count), self.lab() as root:
                value = spec(root, cases=count, n_min=floor)
                round_path = self.round(root, value)
                observations = {
                    row["unit_id"]: dict(correct=not (
                        row["arm"] == "A" and row["case_id"] == "x1"))
                    for row in value["order"]}
                self.complete(root, round_path, value, observations)
                result, path = self.compute(root, round_path, "success", pure=True)
                normal = self.decision(result, "supported", wins=1, losses=0,
                                       valid=count, required=count)
                self.assertEqual(normal["defects"], dict(baseline=0, candidate=0))
                self.replay(root, round_path, path, "success")
                # JSON object/whitespace order is a valid equivalent spec.
                alternate = root / "equivalent.spec.json"
                alternate.write_text(json.dumps(value, sort_keys=False, indent=3) + "\n")
                sibling = root / "equivalent"
                self.cli(root, "seal", "--spec", alternate, "--round", sibling)
                self.assertEqual(
                    (sibling / "manifest.json").read_bytes(),
                    (round_path / "manifest.json").read_bytes())

        # distinct comparison thresholds and unpooled strata.
        for changed_c in (False, True):
            with self.subTest(changed_c=changed_c), self.lab() as root:
                value = spec(root, arms=("A", "B", "C"),
                             strata=("low", "medium"), win_min=2)
                round_path = self.round(root, value)
                correctness = {
                    ("low", "A"): [False, False],
                    ("low", "B"): [True, True],
                    ("low", "C"): [True, True],
                    ("medium", "A"): [False, False],
                    ("medium", "B"): [True, False],
                    ("medium", "C"): [False, True] if changed_c else [True, True]}
                observations = {
                    row["unit_id"]: dict(correct=correctness[
                        (row["stratum"], row["arm"])][int(row["case_id"][1:]) - 1])
                    for row in value["order"]}
                self.complete(root, round_path, value, observations)
                result, path = self.compute(root, round_path, "inconclusive")
                self.assertEqual(len(result["comparisons"]), 4)
                for comparison, stratum, outcome, wins, losses in (
                        ("B/A", "low", "supported", 2, 0),
                        ("C/B", "low", "tie", 0, 0),
                        ("B/A", "medium", "tie", 1, 0),
                        ("C/B", "medium", "reject" if changed_c else "supported",
                         1, 1 if changed_c else 0)):
                    self.decision(result, outcome, comparison=comparison,
                                  stratum=stratum, wins=wins, losses=losses,
                                  valid=2, required=2)
                self.replay(root, round_path, path, "inconclusive")

        # integer ratio boundary, separate from long wait fixtures.
        timing = [
            ("ratio-equality", [200, 200], [250, 250], [0, 0], "supported", "success"),
            ("ratio-over", [200, 200], [250, 251], [0, 0], "reject", "success"),
            ("wait-sum-valid", [30000, 30000], [30000, 30000],
             [15000, 15000], "supported", "success"),
            ("one-wait-over", [30000, 30000], [30000, 30000],
             [15000, 20001], "reject", "success"),
            ("unknown-wall", [30000, 30000], [30000, None],
             [15000, 15000], "inconclusive", "inconclusive"),
            ("unknown-wait", [30000, 30000], [30000, 30000],
             [15000, None], "inconclusive", "inconclusive")]
        for label, baseline, candidate, waits, decision, state in timing:
            with self.subTest(timing=label), self.lab() as root:
                value = spec(root, ratio=dict(numerator=5, denominator=4),
                             wait_cap=20000)
                round_path = self.round(root, value)
                observations = {}
                for row in value["order"]:
                    index = int(row["case_id"][1:]) - 1
                    wall = (baseline if row["arm"] == "A" else candidate)[index]
                    observations[row["unit_id"]] = dict(
                        correct=row["arm"] == "B", wall=wall,
                        wait=0 if row["arm"] == "A" else waits[index],
                        # Unknown optional timing is not unknown budget usage.
                        usage=dict(episodes=1, turns=5, judgment_requests=0,
                                   wall_ms=100 if wall is None else wall))
                self.complete(root, round_path, value, observations)
                result, path = self.compute(root, round_path, state)
                unknown_timing = label in ("unknown-wall", "unknown-wait")
                cell = self.decision(result, decision,
                                     wins=1 if unknown_timing else 2, losses=0,
                                     valid=1 if unknown_timing else 2, required=2)
                self.assertEqual(cell["missing_cases"], ["x2"] if unknown_timing else [])
                self.assertEqual(
                    {pair["case_id"]: pair["status"] for pair in result["pairs"]},
                    {"x1": "complete", "x2": "unknown" if unknown_timing else "complete"})
                unknown_pair = result["pairs"][1]
                self.assertEqual(unknown_pair["candidate"]["wall_ms"], candidate[1])
                self.assertEqual(unknown_pair["candidate"]["additional_judgment_wait_ms"], waits[1])
                if label.startswith("ratio"):
                    self.assertEqual(cell["wall_ms"], dict(
                        baseline=400, candidate=500 if label == "ratio-equality" else 501))
                self.replay(root, round_path, path, state)

        # The stated defect-benefit branch is a real computed alternative.
        with self.lab() as root:
            value = spec(root)
            round_path = self.round(root, value)
            observations = {row["unit_id"]: dict(
                correct=True, defects=1 if row["arm"] == "A" else 0)
                for row in value["order"]}
            self.complete(root, round_path, value, observations)
            result, path = self.compute(root, round_path, "success")
            cell = self.decision(result, "supported", wins=0, losses=0, valid=2)
            self.assertEqual(cell["defects"], dict(baseline=2, candidate=0))
            self.replay(root, round_path, path, "success")

        # observe actual nonempty exclusions, not just its JSON key.
        with self.lab() as root:
            value = spec(root, cases=3)
            value["order"] = [row for row in value["order"]
                              if row["unit_id"] != "low-x3-B"]
            smoke = copy.deepcopy(value["order"][0])
            smoke.update(unit_id="smoke-low-x1-A", stage="smoke")
            value["order"].insert(0, smoke)
            round_path = self.round(root, value)
            self.complete(root, round_path, value, {
                row["unit_id"]: dict(correct=row["arm"] == "B")
                for row in value["order"]})
            result, path = self.compute(
                root, round_path, "success", pair_cases=("x1", "x2"), exclusions=(
                    dict(comparison_id="B/A", stratum_id="low", case_id="x1",
                         unit_id="smoke-low-x1-A", reason="smoke"),
                    dict(comparison_id="B/A", stratum_id="low", case_id="x3",
                         unit_id="low-x3-A", reason="unpaired-measurement")))
            self.decision(result, "supported", wins=2, losses=0, valid=2, required=2)
            self.replay(root, round_path, path, "success")

    def test_seal_chain_and_receipt_faults_never_manufacture_green(self):
        # Positive native control precedes every family of expected refusals.
        with self.lab() as root:
            value = spec(root, cases=1, n_min=1)
            round_path = self.round(root, value)
            self.complete(root, round_path, value, {
                row["unit_id"]: dict(correct=row["arm"] == "B")
                for row in value["order"]})
            result, path = self.compute(root, round_path, "success")
            self.decision(result, "supported", wins=1, losses=0, valid=1)
            self.replay(root, round_path, path, "success")
            wrong = copy.deepcopy(result)
            wrong["comparisons"][0]["decision"] = "tie"
            expected_path = put(root / "wrong-expected-result.json", wrong)
            self.replay(root, round_path, expected_path, "success", expected_match=False)

        for fault in ("floor", "schema", "unknown-field", "rule", "hash",
                      "duplicate-case", "boolean-limit", "plugin", "escape"):
            with self.subTest(seal_fault=fault), self.lab() as root:
                value = spec(root, cases=1, n_min=1)
                if fault == "floor":
                    value["comparisons"][0]["decision_rule"]["n_min"] = 2
                elif fault == "schema":
                    value["schema"] = "unsupported"
                elif fault == "unknown-field":
                    value["unknown"] = True
                elif fault == "rule":
                    value["comparisons"][0]["decision_rule"]["name"] = "arbitrary-code"
                elif fault == "hash":
                    value["inputs"][0]["sha256"] = "0" * 64
                elif fault == "duplicate-case":
                    value["cases"].append(copy.deepcopy(value["cases"][0]))
                elif fault == "boolean-limit":
                    value["budgets"]["turns"]["limit"] = True
                elif fault == "plugin":
                    value["plugin"] = "do-not-execute.py"
                    (root / "do-not-execute.py").write_text(
                        'raise AssertionError("plugin must not execute")\n')
                elif fault == "escape":
                    value["inputs"][0]["path"] = "../outside-public.json"
                specification = put(root / "bad.spec.json", value)
                self.cli(root, "seal", "--spec", specification,
                         "--round", root / "rejected", expected=(2,))
                self.assertFalse((root / "rejected").exists())

        for malformed in ("duplicate-json-key", "nonfinite-json"):
            with self.subTest(json=malformed), self.lab() as root:
                value = spec(root)
                if malformed == "duplicate-json-key":
                    raw = b'{"round_id":"duplicate",' + canonical(value)[1:]
                else:
                    value["budgets"]["turns"]["limit"] = float("nan")
                    raw = json.dumps(value, allow_nan=True).encode()
                source = root / "malformed.json"
                source.write_bytes(raw)
                self.cli(root, "seal", "--spec", source,
                         "--round", root / "rejected", expected=(2,))
                self.assertFalse((root / "rejected").exists())

        with self.lab() as root:
            value = spec(root)
            specification = put(root / "spec.json", value)
            round_path = self.seal(root, value)
            before = inventory(round_path)
            self.cli(root, "seal", "--spec", specification,
                     "--round", round_path, expected=(2,))
            self.assertEqual(inventory(round_path), before)
            symlink = root / "linked-input.json"
            symlink.symlink_to(root / value["inputs"][0]["path"])
            value["inputs"][0]["path"] = symlink.name
            put(specification, value)
            self.cli(root, "seal", "--spec", specification,
                     "--round", root / "rejected-link", expected=(2,))
            self.assertFalse((root / "rejected-link").exists())
            output = root / "linked-output"
            output.symlink_to(round_path, target_is_directory=True)
            self.cli(root, "compute", "--round", round_path,
                     "--output", output, expected=(2,))
            self.assertEqual(inventory(round_path), before)
            self.cli(root, "compute", "--round", round_path,
                     "--output", round_path / "inside-evidence", expected=(2,))
            self.assertEqual(inventory(round_path), before)

        for fault in ("seal", "threshold", "input", "chain", "receipt"):
            with self.subTest(retained_fault=fault), self.lab() as root:
                value = spec(root)
                round_path = self.round(root, value)
                _, _, first_start = self.start(root, round_path, value["order"][0]["unit_id"])
                _, finish_path, finish = self.finish(root, round_path, value["order"][0])
                if fault in ("seal", "threshold"):
                    manifest_path = round_path / "manifest.json"
                    manifest = json.loads(manifest_path.read_bytes())
                    if fault == "seal":
                        manifest["seal_sha256"] = "f" * 64
                    else:
                        manifest["comparisons"][0]["decision_rule"]["n_min"] = 1
                    put(manifest_path, manifest)
                elif fault == "input":
                    (root / value["inputs"][0]["path"]).write_bytes(b"changed public input")
                elif fault == "chain":
                    with sqlite3.connect(round_path / "round.sqlite") as connection:
                        connection.execute("UPDATE events SET previous_sha256=? WHERE sequence=1",
                                           ("f" * 64,))
                else:
                    (root / finish["payload"]["receipt"]["path"]).write_bytes(b"changed receipt")
                before = inventory(round_path)
                self.cli(root, "compute", "--round", round_path,
                         "--output", root / "refused", expected=(2,))
                self.assertEqual(inventory(round_path), before)

        with self.lab() as root:
            value = spec(root)
            round_path = self.round(root, value)
            first, event, body = self.start(root, round_path, value["order"][0]["unit_id"])
            count = self.database_count(round_path)
            # Byte/canonical equivalent event is idempotent, conflicting same ID is not.
            event.write_text(json.dumps(body, indent=4) + "\n")
            duplicate = self.record(root, round_path, event)
            self.assertEqual(duplicate["state"], "already-recorded")
            self.assertFalse(duplicate["dispatch_allowed"])
            self.assertEqual(duplicate["event_sha256"], first["event_sha256"])
            self.assertEqual(duplicate["sequence"], first["sequence"])
            self.assertEqual(self.database_count(round_path), count)
            changed = copy.deepcopy(body)
            changed["actor"] = "conflicting-actor"
            put(event, changed)
            self.record(root, round_path, event, expected=(2,))
            self.assertEqual(self.database_count(round_path), count)
            _, out_of_order = self.event(root, round_path, "start",
                                          unit=value["order"][2]["unit_id"])
            out_path = put(root / "out-of-order.json", out_of_order)
            self.record(root, round_path, out_path, expected=(2,))
            self.assertEqual(self.database_count(round_path), count)
            terminal, terminal_path, terminal_body = self.finish(
                root, round_path, value["order"][0], correct=True)
            finished_count = self.database_count(round_path)
            repeated_terminal = self.record(root, round_path, terminal_path)
            self.assertEqual(repeated_terminal["state"], "already-recorded")
            self.assertFalse(repeated_terminal["dispatch_allowed"])
            conflicting = copy.deepcopy(terminal_body)
            conflicting["event_id"] = str(uuid.uuid4())
            conflicting["payload"]["scores"]["correct"] = False
            path = put(root / "conflicting-terminal.json", conflicting)
            self.record(root, round_path, path, expected=(2,))
            self.assertEqual(self.database_count(round_path), finished_count)

        # Native failure remains a failure even with a final misleading PASS.
        with self.lab() as root:
            bad = put(root / "bad.json", {"schema": "invalid"})
            wrapper = (
                "import subprocess,sys; "
                "r=subprocess.run(sys.argv[1:]); print('PASS'); sys.exit(r.returncode)")
            child = self.run_child(root, [
                sys.executable, "-I", "-c", wrapper, sys.executable, "-I",
                str(SCRIPT), "seal", "--spec", str(bad), "--round", str(root / "out")], (2,))
            self.assertIn(b"PASS", child.stdout)
            self.assertFalse((root / "out").exists())


        # Recheck sealed public bytes before issuing a new dispatch ticket.
        for input_id in ("public", "binding", "procedure"):
            for changed in (False, True):
                with self.subTest(public_input=input_id, changed=changed), self.lab() as root:
                    value = spec(root, cases=1, n_min=1)
                    round_path = self.round(root, value)
                    event, _ = self.event(root, round_path, "start",
                                          unit=value["order"][0]["unit_id"])
                    entry = next(row for row in value["inputs"] if row["id"] == input_id)
                    if changed:
                        (root / entry["path"]).write_bytes(b"changed admitted public fixture\n")
                    count, before = self.database_count(round_path), inventory(round_path)
                    if changed:
                        child = self.record(root, round_path, event, expected=(2,))
                        self.assertEqual(child.returncode, 2)
                        self.assertEqual(self.database_count(round_path), count)
                        self.assertEqual(inventory(round_path), before)
                    else:
                        recorded = self.record(root, round_path, event)
                        self.assertTrue(recorded["dispatch_allowed"])
                        self.assertEqual(self.database_count(round_path), count + 1)
                        self.finish(root, round_path, value["order"][0], correct=False)
                        self.complete(root, round_path, value, rows=value["order"][1:])
                        result, path = self.compute(root, round_path, "success")
                        self.decision(result, "supported", wins=1, losses=0, valid=1)
                        self.replay(root, round_path, path, "success")

        # Refuse aliases before opening a store; every target stays in this lab.
        for form in ("real", "round-alias", "manifest-alias", "database-alias", "outside-cwd"):
            with self.subTest(store_path=form), self.lab() as root:
                value = spec(root, cases=1, n_min=1)
                round_path = self.round(root, value)
                event, _ = self.event(root, round_path, "start",
                                      unit=value["order"][0]["unit_id"])
                aliases, targets = root / "aliases", root / "alias-targets"
                aliases.mkdir()
                targets.mkdir()
                submitted_round, operation_cwd, submitted_event = round_path, root, event
                if form == "round-alias":
                    submitted_round = aliases / "round"
                    submitted_round.symlink_to(round_path, target_is_directory=True)
                elif form in ("manifest-alias", "database-alias"):
                    filename = "manifest.json" if form == "manifest-alias" else "round.sqlite"
                    member, target = round_path / filename, targets / filename
                    member.rename(target)
                    member.symlink_to(target)
                elif form == "outside-cwd":
                    operation_cwd = root / "operation-cwd"
                    operation_cwd.mkdir()
                    shutil.copytree(root / "public", operation_cwd / "public")
                    shutil.copytree(root / "receipts", operation_cwd / "receipts")
                    submitted_event = operation_cwd / "start.json"
                    submitted_event.write_bytes(event.read_bytes())
                protected = [round_path, aliases, targets, root / "public", root / "receipts"]
                if operation_cwd != root:
                    protected += [operation_cwd / "public", operation_cwd / "receipts"]
                before = {str(path): inventory(path) for path in protected}
                count = self.database_count(round_path)
                if form == "real":
                    recorded = self.record(root, round_path, event)
                    self.assertTrue(recorded["dispatch_allowed"])
                    self.finish(root, round_path, value["order"][0], correct=False)
                    self.complete(root, round_path, value, rows=value["order"][1:])
                    result, path = self.compute(root, round_path, "success")
                    self.decision(result, "supported", wins=1, losses=0, valid=1)
                    self.replay(root, round_path, path, "success")
                else:
                    child = self.cli(operation_cwd, "record", "--round", submitted_round,
                                     "--event", submitted_event, expected=(2,))
                    self.assertEqual(child.returncode, 2)
                    self.assertEqual(self.database_count(round_path), count)
                    self.assertEqual({str(path): inventory(path) for path in protected}, before)

    def test_unknown_interruption_and_terminal_states_preserve_limits(self):
        # n_min met is not permission to omit the third required pair.
        for terminal in ("pending", "closed", "complete"):
            with self.subTest(missing_pair=terminal), self.lab() as root:
                value = spec(root, cases=3, n_min=2)
                round_path = self.round(root, value)
                observations = {row["unit_id"]: dict(
                    correct=row["arm"] == "B" or row["case_id"] == "x3")
                    for row in value["order"]}
                self.complete(root, round_path, value, observations, rows=value["order"][:4])
                if terminal == "closed":
                    self.stop(root, round_path, "inconclusive")
                elif terminal == "complete":
                    self.complete(root, round_path, value, observations, rows=value["order"][4:])
                state = dict(pending="running", closed="inconclusive",
                             complete="success")[terminal]
                result, path = self.compute(root, round_path, state)
                cell = self.decision(result,
                    "supported" if terminal == "complete" else "inconclusive",
                    wins=2, losses=0, valid=3 if terminal == "complete" else 2, required=3)
                self.assertEqual(cell["missing_cases"], [] if terminal == "complete" else ["x3"])
                self.assertEqual(
                    {pair["case_id"]: pair["status"] for pair in result["pairs"]},
                    {"x1": "complete", "x2": "complete",
                     "x3": "complete" if terminal == "complete" else "missing"})
                self.replay(root, round_path, path, state)

        # A committed start reserves before any external effect and survives no finish.
        for when in ("before", "after"):
            with self.subTest(commit_interruption=when), self.lab() as root:
                value = spec(root)
                round_path = self.round(root, value)
                count = self.database_count(round_path)
                event, body = self.event(root, round_path, "start",
                                         unit=value["order"][0]["unit_id"])
                self.run_child(root, [sys.executable, "-I", "-c", CRASH_BOOTSTRAP,
                                      str(SCRIPT), when, str(round_path), str(event)], (99,))
                # Authorized record performs normal SQLite recovery if necessary.
                receipt = self.record(root, round_path, event)
                self.assertEqual(receipt["state"],
                                 "recorded" if when == "before" else "already-recorded")
                self.assertEqual(receipt["dispatch_allowed"], when == "before")
                self.assertEqual(self.database_count(round_path), count + 1)
                result, path = self.compute(root, round_path, "running")
                for dimension in DIMENSIONS:
                    budget = result["budgets"][dimension]
                    self.assertEqual(budget["started_reserved"], RESERVATION[dimension])
                    self.assertEqual(budget["remaining"],
                                     value["budgets"][dimension]["limit"] - RESERVATION[dimension])
                    self.assertEqual(budget["active_reserved"] + budget["unknown_reserved"],
                                     RESERVATION[dimension])
                self.start(root, round_path, value["order"][1]["unit_id"], expected=(2,))
                self.replay(root, round_path, path, "running")

        # Unknown consumption is retained, reconciled once, never silently refunded.
        with self.lab() as root:
            value = spec(root)
            round_path = self.round(root, value)
            row = value["order"][0]
            self.start(root, round_path, row["unit_id"])
            receipt, _, unknown = self.finish(
                root, round_path, row, status="unknown",
                usage={key: None for key in DIMENSIONS}, corrections=1)
            before_count = self.database_count(round_path)
            result, _ = self.compute(root, round_path, "infrastructure-failure")
            self.assertEqual(result["budgets"]["episodes"]["unknown_reserved"], 1)
            self.assertEqual(result["summary"]["corrections"], 1)
            # A's unknown terminal and B's absent terminal still make a missing pair.
            self.assertEqual(result["pairs"][0]["status"], "missing")
            self.assertIsNone(result["pairs"][0]["baseline"])
            self.start(root, round_path, value["order"][1]["unit_id"], expected=(2,))
            reconciled_receipt, reconciled_event, _ = self.finish(
                root, round_path, row, kind="reconcile",
                prior=receipt["event_sha256"], correct=True)
            reconciled, path = self.compute(root, round_path, "running")
            self.assertEqual(reconciled["budgets"]["episodes"]["started_reserved"], 1)
            self.assertEqual(reconciled["budgets"]["episodes"]["remaining"], 3)
            self.assertEqual(reconciled["summary"]["corrections"], 1)
            self.assertEqual(self.database_count(round_path), before_count + 1)
            self.replay(root, round_path, path, "running")
            repeated = self.record(root, round_path, reconciled_event)
            self.assertEqual(repeated["state"], "already-recorded")
            self.assertFalse(repeated["dispatch_allowed"])
            self.assertEqual(repeated["event_sha256"], reconciled_receipt["event_sha256"])
            self.assertEqual(self.database_count(round_path), before_count + 1)
            # uncertainty can resolve without a successor or counter reset.
            observations = {entry["unit_id"]: dict(correct=entry["arm"] == "B")
                            for entry in value["order"][1:]}
            self.complete(root, round_path, value, observations, rows=value["order"][1:])
            recovered, recovered_path = self.compute(root, round_path, "success")
            self.decision(recovered, "supported", wins=1, losses=0, valid=2, required=2)
            self.assertEqual(recovered["summary"]["corrections"], 1)
            self.assertEqual(recovered["summary"]["reserved"]["episodes"], 4)
            self.assertEqual(recovered["summary"]["known_consumed"]["episodes"], 4)
            self.assertEqual(recovered["summary"]["unknown"]["episodes"], 0)
            self.assertEqual(recovered["budgets"]["episodes"]["remaining"], 0)
            self.replay(root, round_path, recovered_path, "success")

        # Higher priority safety/infra faults cannot be hidden by n_min/pending data.
        for fault, state in (("safety", "aborted"), ("critical-unknown", "infrastructure-failure"),
                             ("overrun", "infrastructure-failure"),
                             ("known-infrastructure", "infrastructure-failure")):
            with self.subTest(priority=fault), self.lab() as root:
                value = spec(root, cases=3)
                round_path = self.round(root, value)
                first, candidate = value["order"][:2]
                self.start(root, round_path, first["unit_id"])
                self.finish(root, round_path, first, correct=False)
                self.start(root, round_path, candidate["unit_id"])
                arguments = (dict(safety="violated") if fault == "safety" else
                             dict(safety="unknown") if fault == "critical-unknown" else
                             dict(status="infrastructure-failure") if fault == "known-infrastructure" else
                             dict(usage=dict(episodes=1, turns=21,
                                             judgment_requests=0, wall_ms=100)))
                terminal, _, body = self.finish(root, round_path, candidate, **arguments)
                result, path = self.compute(root, round_path, state)
                if fault == "safety":
                    self.decision(result, "reject")
                if fault == "critical-unknown":
                    self.assertEqual(result["pairs"][0]["status"], "unknown")
                    self.assertEqual(result["pairs"][0]["candidate"]["safety"], "unknown")
                else:
                    # Known safety/usage/status facts cannot be overwritten by reconcile.
                    changed = copy.deepcopy(body)
                    changed["event_id"] = str(uuid.uuid4())
                    changed["kind"] = "reconcile"
                    changed["payload"]["prior_event_sha256"] = terminal["event_sha256"]
                    if fault == "safety":
                        changed["payload"]["scores"]["safety"] = "preserved"
                    elif fault == "overrun":
                        changed["payload"]["usage"]["turns"] = 5
                    else:
                        changed["payload"]["status"] = "success"
                    count = self.database_count(round_path)
                    self.record(root, round_path,
                                put(root / "erase-known-fact.json", changed), expected=(2,))
                    self.assertEqual(self.database_count(round_path), count)
                self.start(root, round_path, value["order"][2]["unit_id"], expected=(2,))
                self.replay(root, round_path, path, state)

        for status in ("missing", "fail", "unavailable"):
            with self.subTest(qualification=status), self.lab() as root:
                value = spec(root)
                round_path = self.seal(root, value)
                if status != "missing":
                    self.qualify(root, round_path, status)
                result, path = self.compute(root, round_path, "not-run")
                self.assertEqual(result["budgets"]["episodes"]["started_reserved"], 0)
                self.start(root, round_path, value["order"][0]["unit_id"], expected=(2,))
                self.replay(root, round_path, path, "not-run")

        for state in ("aborted", "infrastructure-failure"):
            with self.subTest(explicit_stop=state), self.lab() as root:
                value = spec(root)
                round_path = self.round(root, value)
                self.stop(root, round_path, state)
                result, path = self.compute(root, round_path, state)
                self.start(root, round_path, value["order"][0]["unit_id"], expected=(2,))
                self.replay(root, round_path, path, state)

        # accepts seal refusal OR safe prefix admission, never an unfunded start.
        # A funded identical neighbor is mandatory, so refusing every seal cannot pass.
        for funded in (False, True):
            with self.subTest(funded_order=funded), self.lab() as root:
                value = spec(root)
                value["budgets"]["turns"]["limit"] = 80 if funded else 35
                specification = put(root / "budget.spec.json", value)
                round_path = root / "round"
                child = self.cli(root, "seal", "--spec", specification,
                                 "--round", round_path,
                                 expected=(0,) if funded else (0, 2))
                if child.returncode == 2:
                    self.assertFalse(round_path.exists())
                    continue
                sealed = self.receipt(child, "seal")
                self.assertEqual(sealed["seal_sha256"],
                                 json.loads((round_path / "manifest.json").read_bytes())["seal_sha256"])
                self.qualify(root, round_path)
                observations = {row["unit_id"]: dict(correct=row["arm"] == "B")
                                for row in value["order"]}
                if funded:
                    self.complete(root, round_path, value, observations)
                    result, path = self.compute(root, round_path, "success")
                    self.decision(result, "supported", wins=2, losses=0, valid=2, required=2)
                    self.assertEqual(result["budgets"]["turns"]["remaining"], 0)
                    self.assertEqual(result["budgets"]["turns"]["known_consumed"], 20)
                    self.replay(root, round_path, path, "success")
                else:
                    row = value["order"][0]
                    self.start(root, round_path, row["unit_id"])
                    self.finish(root, round_path, row, **observations[row["unit_id"]])
                    count, before = self.database_count(round_path), inventory(round_path)
                    self.start(root, round_path, value["order"][1]["unit_id"], expected=(2,))
                    self.assertEqual(self.database_count(round_path), count)
                    self.assertEqual(inventory(round_path), before)
                    self.stop(root, round_path, "inconclusive")
                    result, path = self.compute(root, round_path, "inconclusive")
                    self.assertEqual(result["budgets"]["turns"]["started_reserved"], 20)
                    self.assertEqual(result["budgets"]["turns"]["known_consumed"], 5)
                    self.assertEqual(result["budgets"]["turns"]["remaining"], 15)
                    self.replay(root, round_path, path, "inconclusive")

        # Separately admitted same-pool lineage fixture consumes actual parent summary;
        # it is not required for unknown recovery or authority to hide a known stop.
        with self.lab() as root:
            parent_spec = spec(root, limit=20)
            parent = self.round(root, parent_spec, "parent")
            first, second = parent_spec["order"][:2]
            self.start(root, parent, first["unit_id"])
            self.finish(root, parent, first, corrections=1)
            self.start(root, parent, second["unit_id"])
            self.finish(root, parent, second, status="unknown",
                        usage={key: None for key in DIMENSIONS}, corrections=1)
            self.stop(root, parent, "infrastructure-failure")
            result, parent_path = self.compute(root, parent, "infrastructure-failure")
            self.assertEqual(result["summary"]["reserved"]["episodes"], 2)
            self.assertEqual(result["summary"]["unknown"]["episodes"], 1)
            self.assertEqual(result["summary"]["corrections"], 2)
            self.assertEqual(result["summary"], dict(
                reserved=dict(episodes=2, turns=40, judgment_requests=4, wall_ms=120000),
                known_consumed=dict(episodes=1, turns=5, judgment_requests=0, wall_ms=100),
                unknown=dict(episodes=1, turns=20, judgment_requests=2, wall_ms=60000),
                corrections=2))
            successor = spec(root, cases=1, n_min=1, limit=20)
            summary = result["summary"]
            successor["opening"] = dict(
                reserved=summary["reserved"], known_consumed=summary["known_consumed"],
                unknown=summary["unknown"], corrections=summary["corrections"],
                parent_receipt=ref(root, parent_path), new_allocation_receipt=None)
            successor["lineage"]["parent_result"] = ref(root, parent_path)
            child = self.round(root, successor, "successor")
            self.start(root, child, successor["order"][0]["unit_id"])
            carried, _ = self.compute(root, child, "running")
            self.assertEqual(carried["budgets"]["episodes"]["opening_reserved"], 2)
            self.assertEqual(carried["budgets"]["episodes"]["remaining"], 17)
            self.assertEqual(carried["summary"]["corrections"], 2)
            self.assertEqual(carried["summary"], dict(
                reserved=dict(episodes=3, turns=60, judgment_requests=6, wall_ms=180000),
                known_consumed=dict(episodes=1, turns=5, judgment_requests=0, wall_ms=100),
                unknown=dict(episodes=2, turns=40, judgment_requests=4, wall_ms=120000),
                corrections=2))
            for fault in ("reset", "limit", "missing-parent"):
                bad = copy.deepcopy(successor)
                if fault == "reset":
                    bad["opening"]["reserved"]["episodes"] = 0
                elif fault == "limit":
                    bad["budgets"]["episodes"]["limit"] = 21
                else:
                    bad["lineage"]["parent_result"] = None
                path = put(root / (fault + ".json"), bad)
                self.cli(root, "seal", "--spec", path,
                         "--round", root / ("bad-" + fault), expected=(2,))


        # Status uncertainty does not authorize replacement of known scores.
        for changed_field in (None, "correct", "defects"):
            with self.subTest(known_score=changed_field), self.lab() as root:
                value = spec(root, cases=1, n_min=1)
                round_path = self.round(root, value)
                row = value["order"][0]
                self.start(root, round_path, row["unit_id"])
                observed = put(root / "receipts" / "known-scores.json", {"fixture": "known scores"})
                payload = dict(status="unknown", usage={key: None for key in DIMENSIONS},
                               scores=dict(correct=False, safety="preserved", defects=1,
                                           wall_ms=100, additional_judgment_wait_ms=0),
                               receipt=ref(root, observed), corrections_delta=1)
                event, _ = self.event(root, round_path, "finish", unit=row["unit_id"], payload=payload)
                terminal = self.record(root, round_path, event)
                resolved = copy.deepcopy(payload)
                resolved.update(status="success", corrections_delta=0,
                                usage=dict(episodes=1, turns=5, judgment_requests=0, wall_ms=100),
                                prior_event_sha256=terminal["event_sha256"])
                if changed_field == "correct":
                    resolved["scores"]["correct"] = True
                elif changed_field == "defects":
                    resolved["scores"]["defects"] = 0
                event, _ = self.event(root, round_path, "reconcile", unit=row["unit_id"], payload=resolved)
                count, before = self.database_count(round_path), inventory(round_path)
                if changed_field is not None:
                    self.record(root, round_path, event, expected=(2,))
                    self.assertEqual(self.database_count(round_path), count)
                    self.assertEqual(inventory(round_path), before)
                else:
                    self.record(root, round_path, event)
                    self.assertEqual(self.database_count(round_path), count + 1)
                    recovered, _ = self.compute(root, round_path, "running")
                    self.assertEqual(recovered["summary"]["corrections"], 1)
                    self.complete(root, round_path, value, rows=value["order"][1:])
                    result, path = self.compute(root, round_path, "success")
                    self.decision(result, "supported", wins=1, losses=0, valid=1)
                    self.replay(root, round_path, path, "success")

        # Unknown score fields may resolve, while an observed violation stays terminal.
        for safety in ("unknown", "violated"):
            with self.subTest(score_resolution=safety), self.lab() as root:
                value = spec(root, cases=1, n_min=1)
                round_path = self.round(root, value)
                row = value["order"][0]
                self.start(root, round_path, row["unit_id"])
                observed = put(root / "receipts" / "partial-scores.json", {"fixture": "partial scores"})
                payload = dict(status="unknown", usage={key: None for key in DIMENSIONS},
                               scores=dict(correct=False, safety=safety, defects=0,
                                           wall_ms=None, additional_judgment_wait_ms=None),
                               receipt=ref(root, observed), corrections_delta=1)
                event, _ = self.event(root, round_path, "finish", unit=row["unit_id"], payload=payload)
                terminal = self.record(root, round_path, event)
                self.start(root, round_path, value["order"][1]["unit_id"], expected=(2,))
                resolved = copy.deepcopy(payload)
                resolved.update(status="success", corrections_delta=0,
                                usage=dict(episodes=1, turns=5, judgment_requests=0, wall_ms=100),
                                prior_event_sha256=terminal["event_sha256"])
                resolved["scores"].update(safety="preserved" if safety == "unknown" else "violated",
                                          wall_ms=100, additional_judgment_wait_ms=0)
                event, _ = self.event(root, round_path, "reconcile", unit=row["unit_id"], payload=resolved)
                count = self.database_count(round_path)
                self.record(root, round_path, event)
                state = "running" if safety == "unknown" else "aborted"
                recovered, path = self.compute(root, round_path, state)
                self.assertEqual(self.database_count(round_path), count + 1)
                self.assertEqual(recovered["summary"]["corrections"], 1)
                self.assertEqual(recovered["budgets"]["episodes"]["started_reserved"], 1)
                self.assertEqual(recovered["budgets"]["episodes"]["remaining"], 1)
                if safety == "violated":
                    count, before = self.database_count(round_path), inventory(round_path)
                    self.start(root, round_path, value["order"][1]["unit_id"], expected=(2,))
                    self.assertEqual(self.database_count(round_path), count)
                    self.assertEqual(inventory(round_path), before)
                    self.decision(recovered, "reject")
                    self.replay(root, round_path, path, state)
                else:
                    self.complete(root, round_path, value, rows=value["order"][1:])
                    result, path = self.compute(root, round_path, "success")
                    self.decision(result, "supported", wins=1, losses=0, valid=1)
                    self.replay(root, round_path, path, "success")

        # Newly resolved actual usage is retained even when it exceeds its reservation.
        for turns in (5, 21):
            with self.subTest(reconciled_turns=turns), self.lab() as root:
                value = spec(root, cases=1, n_min=1)
                round_path = self.round(root, value)
                row = value["order"][0]
                self.start(root, round_path, row["unit_id"])
                terminal, _, _ = self.finish(root, round_path, row, status="unknown",
                                             usage={key: None for key in DIMENSIONS}, corrections=1)
                count = self.database_count(round_path)
                reconciled, _, _ = self.finish(
                    root, round_path, row, kind="reconcile", prior=terminal["event_sha256"],
                    correct=False, usage=dict(episodes=1, turns=turns, judgment_requests=0, wall_ms=100))
                self.assertFalse(reconciled["dispatch_allowed"])
                self.assertEqual(self.database_count(round_path), count + 1)
                state = "running" if turns == 5 else "infrastructure-failure"
                result, path = self.compute(root, round_path, state)
                self.assertEqual(result["summary"]["known_consumed"]["turns"], turns)
                self.assertEqual(result["summary"]["corrections"], 1)
                self.assertEqual(result["budgets"]["turns"]["started_reserved"], 20)
                self.assertEqual(result["budgets"]["turns"]["remaining"], 20)
                self.assertEqual(result["summary"]["unknown"]["turns"], 0)
                if turns == 21:
                    count, before = self.database_count(round_path), inventory(round_path)
                    self.start(root, round_path, value["order"][1]["unit_id"], expected=(2,))
                    self.assertEqual(self.database_count(round_path), count)
                    self.assertEqual(inventory(round_path), before)
                    self.replay(root, round_path, path, state)
                else:
                    self.complete(root, round_path, value, rows=value["order"][1:])
                    result, path = self.compute(root, round_path, "success")
                    self.decision(result, "supported", wins=1, losses=0, valid=1)
                    self.replay(root, round_path, path, "success")

    def test_concurrent_recorders_commit_at_most_one_next_start(self):
        with self.lab() as root:
            value = spec(root)
            round_path = self.round(root, value)
            count = self.database_count(round_path)
            events = [self.event(root, round_path, "start",
                                 unit=value["order"][0]["unit_id"])[0] for _ in range(2)]
            submitted_events = [strict_json(event.read_bytes()) for event in events]
            database = round_path / "round.sqlite"
            # A held real writer transaction causes explicit busy, no retry/charge.
            connection = sqlite3.connect(database, timeout=0)
            connection.execute("BEGIN IMMEDIATE")
            try:
                self.record(root, round_path, events[0], expected=(3,))
                before = inventory(round_path)
                child = self.cli(root, "compute", "--round", round_path,
                                 "--output", root / "during-writer", expected=(1, 3))
                self.assertEqual(inventory(round_path), before)
                if child.returncode == 1:
                    result = json.loads((root / "during-writer/result.json").read_bytes())
                    self.assertEqual(result["round_state"], "not-run")
                    self.assertEqual(result["event_head_sha256"],
                                     self.database_head(round_path, result["seal_sha256"]))
                    self.assertEqual(result["budgets"]["episodes"]["started_reserved"], 0)
            finally:
                connection.rollback()
                connection.close()
            self.assertEqual(self.database_count(round_path), count)

            gate = root / "release-race"
            ready = [root / ("ready-%d" % index) for index in range(2)]
            started = time.time_ns()
            children = [subprocess.Popen(
                [sys.executable, "-I", "-c", RACE_BOOTSTRAP, str(SCRIPT),
                 str(round_path), str(event), str(marker), str(gate)],
                cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for event, marker in zip(events, ready)]
            deadline = time.monotonic() + 10
            try:
                while not all(path.exists() for path in ready):
                    self.assertLess(time.monotonic(), deadline, "race startup incomplete")
                    time.sleep(.01)
                gate.write_bytes(b"go")
                captures = []
                for child in children:
                    stdout, stderr = child.communicate(timeout=30)
                    captures.append((child.returncode, stdout, stderr))
                self.assertEqual(sum(code == 0 for code, _, _ in captures), 1, captures)
                self.assertTrue(all(code in (0, 2, 3) for code, _, _ in captures), captures)
                winners = []
                for index, (code, stdout, stderr) in enumerate(captures):
                    put(root / ("race-%d.json" % index), dict(
                        argv=children[index].args, cwd=str(root), runtime=sys.version,
                        actor="public-native-fixture", model="n/a", effort="n/a",
                        source_sha256=digest(SCRIPT.read_bytes()),
                        test_sha256=digest(Path(__file__).read_bytes()),
                        start_ns=started, end_ns=time.time_ns(), exit=code,
                        signal=-code if code < 0 else None, timeout=False,
                        stdout_sha256=digest(stdout), stderr_sha256=digest(stderr)))
                    (root / ("race-%d.stdout" % index)).write_bytes(stdout)
                    (root / ("race-%d.stderr" % index)).write_bytes(stderr)
                    if code == 0:
                        child_receipt = subprocess.CompletedProcess(
                            args=children[index].args, returncode=code,
                            stdout=stdout, stderr=stderr)
                        receipt = self.receipt(child_receipt, "record")
                        self.assert_record_identity(round_path, submitted_events[index], receipt)
                        self.assertTrue(receipt["dispatch_allowed"])
                        winners.append(index)
                self.assertEqual(self.database_count(round_path), count + 1)
                duplicate = self.record(root, round_path, events[winners[0]])
                self.assertEqual(duplicate["state"], "already-recorded")
                self.assertFalse(duplicate["dispatch_allowed"])
                result, path = self.compute(root, round_path, "running")
                self.assertEqual(result["budgets"]["episodes"]["started_reserved"], 1)
                self.assertEqual(result["budgets"]["episodes"]["remaining"], 3)
                self.replay(root, round_path, path, "running")
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()
                        child.communicate(timeout=5)


if __name__ == "__main__":
    unittest.main()
