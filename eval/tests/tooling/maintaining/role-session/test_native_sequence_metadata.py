import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

# Set this to a fresh absolute path to retain a second, otherwise identical run.
EVIDENCE_ROOT = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_role_session_check as legacy


SCRIPT = legacy.SCRIPT.resolve()
REPO_ROOT = SCRIPT.parent.parent
MODEL = "gpt-6.1-sol"
EFFORT = "high"
TIER = "priority"
PACKET = b"Sealed reviewer packet.\n"
SEQUENCE_KEYS = {"history_sequence", "sampled_through_sequence"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def renumber(records):
    for index, record in enumerate(records):
        record["ordinal"] = index
    return records


def add_sequences(records):
    records = copy.deepcopy(records)
    history = 0
    for record in records:
        if record["type"] == "response_item":
            record.setdefault("metadata", {}).update({
                "history_sequence": history,
                "sampled_through_sequence": 0,
            })
            history += 1
    return records


def response_items(records):
    return [record for record in records if record["type"] == "response_item"]


def find_record(records, kind, payload_type=None):
    return next(
        record for record in records
        if record["type"] == kind
        and (payload_type is None or record["payload"].get("type") == payload_type)
    )


def insert_after_dispatch(records, additions):
    dispatch = find_record(records, "response_item", "agent_message")
    index = records.index(dispatch) + 1
    records[index:index] = additions
    return renumber(records)


def configuration_record():
    return {
        "timestamp": "2026-01-01T00:00:00Z",
        "type": "response_item",
        "payload": {
            "type": "configuration_update",
            "reasoning": {"effort": EFFORT},
        },
        "metadata": {
            "client_authored": False,
            "harness_authored_configuration": True,
        },
    }


def startup_hash(records):
    inputs = []
    for record in records:
        if record["type"] != "response_item":
            continue
        payload = record["payload"]
        if payload.get("type") == "agent_message":
            break
        if payload.get("type") == "message" and payload.get("role") in ("developer", "user"):
            inputs.append([payload["role"], payload["content"]])
    canonical = json.dumps(
        inputs, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return digest(canonical)


def reader_records(packet_path):
    records = legacy.native_fixture()
    source = (
        'text((await tools.exec_command({cmd:"/bin/cat '
        + str(packet_path)
        + '",login:false,max_output_tokens:20000})).output);'
    )
    packet_text = PACKET.decode("utf-8")
    common = {"turn_id": legacy.TURN}
    additions = [
        {
            "type": "response_item",
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {
                "type": "custom_tool_call",
                "id": "reader-call",
                "status": "completed",
                "call_id": "reader-correlation",
                "name": "exec",
                "input": source,
                "internal_chat_message_metadata_passthrough": dict(common),
            },
        },
        {
            "type": "event_msg",
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {
                "type": "item_completed",
                "thread_id": legacy.THREAD,
                "turn_id": legacy.TURN,
                "item": {
                    "type": "CommandExecution",
                    "id": "reader-effect",
                    "process_id": "reader-process",
                    "command": ["/bin/zsh", "-c", "/bin/cat " + str(packet_path)],
                    "cwd": "file://" + legacy.CWD,
                    "parsed_cmd": [
                        {"type": "unknown", "cmd": "/bin/cat " + str(packet_path)}
                    ],
                    "source": "unified_exec_startup",
                    "status": "completed",
                    "aggregated_output": packet_text,
                    "exit_code": 0,
                    "duration": {"secs": 0, "nanos": 1},
                },
            },
        },
        {
            "type": "response_item",
            "timestamp": "2026-01-01T00:00:00Z",
            "payload": {
                "type": "custom_tool_call_output",
                "id": "reader-output",
                "call_id": "reader-correlation",
                "output": [
                    {
                        "type": "input_text",
                        "text": "Script completed\nWall time 0.1 seconds\nOutput:\n",
                    },
                    {"type": "input_text", "text": packet_text},
                ],
                "internal_chat_message_metadata_passthrough": dict(common),
            },
        },
    ]
    return insert_after_dispatch(records, additions)


class NativeSequenceMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retained_root = None
        if EVIDENCE_ROOT is not None:
            root = Path(EVIDENCE_ROOT)
            if not root.is_absolute():
                raise ValueError("EVIDENCE_ROOT must be an absolute fresh path")
            root.mkdir(parents=True, exist_ok=False)
            cls.retained_root = root.resolve()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tackle-sequence-")
        self.default_root = Path(self.temporary.name).resolve()
        self.observations = {}
        self.addCleanup(self.temporary.cleanup)

    def invoke(self, case_id, factory, sequence, mutate=None, options=None):
        options = dict(options or {})
        if case_id in self.observations:
            raise AssertionError("duplicate case ID: " + case_id)

        default = self._invoke_at(
            self.default_root, case_id, factory, sequence, mutate, options
        )
        if self.retained_root is not None:
            retained = self._invoke_at(
                self.retained_root, case_id, factory, sequence, mutate, options
            )
            self.assertEqual(
                (default["status"], default["stdout"], default["stderr"]),
                (retained["status"], retained["stdout"], retained["stderr"]),
                case_id,
            )
        return default

    def _invoke_at(self, root, case_id, factory, sequence, mutate, options):
        case_dir = root / case_id
        case_dir.mkdir(parents=False, exist_ok=False)
        packet_path = case_dir / "packet.txt"
        packet_path.write_bytes(PACKET)
        records = factory(packet_path)
        if mutate is not None:
            mutate(records)
        renumber(records)
        if sequence:
            records = add_sequences(records)
        if options.get("after_sequence") is not None:
            options["after_sequence"](records)

        session = case_dir / "session.jsonl"
        raw = b"".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            + b"\n"
            for record in records
        )
        session.write_bytes(raw)
        argv = [
            sys.executable, "-I", "-B", str(SCRIPT), str(session),
            "--native",
            "--model", MODEL,
            "--effort", EFFORT,
            "--agent", legacy.AGENT,
            "--thread", legacy.THREAD,
            "--parent", legacy.PARENT,
            "--cwd", legacy.CWD,
            "--tier", TIER,
            "--sha256", options.get("sha256", digest(raw)),
            "--startup-sha256", options.get("startup_sha256", startup_hash(records)),
            "--forbid-forwarding",
        ]
        if options.get("reader"):
            argv.extend([
                "--reader",
                "--packet", str(packet_path),
                "--packet-sha256", options.get("packet_sha256", digest(PACKET)),
            ])
        if options.get("omit_startup"):
            index = argv.index("--startup-sha256")
            del argv[index:index + 2]
        if options.get("allow_forwarding"):
            argv.remove("--forbid-forwarding")
        if options.get("write_root"):
            argv.extend(["--write-root", options["write_root"]])

        completed = subprocess.run(
            argv, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )
        evidence = {
            "argv": argv,
            "cwd": str(REPO_ROOT),
            "runtime": sys.executable,
            "runtime_version": sys.version,
            "status": completed.returncode,
            "source_sha256": digest(SCRIPT.read_bytes()),
            "input_sha256": digest(raw),
            "packet_sha256": digest(PACKET),
            "session_b64": base64.b64encode(raw).decode("ascii"),
            "packet_b64": base64.b64encode(PACKET).decode("ascii"),
            "stdout_b64": base64.b64encode(completed.stdout).decode("ascii"),
            "stderr_b64": base64.b64encode(completed.stderr).decode("ascii"),
        }
        observation = {
            "status": completed.returncode,
            "stdout": None,
            "stderr": None,
            "evidence": evidence,
        }
        if root == self.default_root:
            self.observations[case_id] = observation
        (case_dir / "stdout.bin").write_bytes(completed.stdout)
        (case_dir / "stderr.bin").write_bytes(completed.stderr)
        (case_dir / "observation.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        observation["stdout"] = completed.stdout.decode("utf-8")
        observation["stderr"] = completed.stderr.decode("utf-8")
        return observation

    @staticmethod
    def base_factory(_packet_path):
        return legacy.native_fixture()

    @staticmethod
    def reader_factory(packet_path):
        return reader_records(packet_path)

    def assert_result(self, result, status, reason=None, forwarded=None):
        self.assertEqual(result["status"], status, result)
        self.assertEqual(result["stderr"], "", result)
        payload = json.loads(result["stdout"])
        if status == 2:
            self.assertEqual(payload, {"error": reason})
        else:
            self.assertIn("problems", payload)
            if reason is None:
                self.assertEqual(payload["problems"], [])
            else:
                self.assertIn(reason, payload["problems"])
            if forwarded is not None:
                self.assertEqual(payload["forwarded"], forwarded)
        return payload

    def assert_pair(
        self, name, factory=None, mutate=None, options=None,
        status=1, reason=None, forwarded=None,
    ):
        factory = factory or self.base_factory
        old = self.invoke(name + "-legacy", factory, False, mutate, options)
        new = self.invoke(name + "-sequence", factory, True, mutate, options)
        self.assertEqual(
            (old["status"], old["stdout"], old["stderr"]),
            (new["status"], new["stdout"], new["stderr"]),
            name,
        )
        self.assert_result(old, status, reason, forwarded)
        self.assert_result(new, status, reason, forwarded)

    def test_positive_legacy_and_sequence(self):
        self.assert_pair("tool-free", status=0, forwarded=0)
        self.assert_pair(
            "reader", factory=self.reader_factory, options={"reader": True},
            status=0, forwarded=0,
        )

        def equal_sampled(records):
            for record in response_items(records):
                record["metadata"]["sampled_through_sequence"] = (
                    record["metadata"]["history_sequence"]
                )

        result = self.invoke(
            "equal-sampled", self.base_factory, True,
            options={"after_sequence": equal_sampled},
        )
        self.assert_result(result, 0, forwarded=0)

    def test_configuration_provenance(self):
        def with_configuration(records):
            insert_after_dispatch(records, [configuration_record()])

        self.assert_pair("configuration-valid", mutate=with_configuration, status=0)

        def invalid_provenance(value, field=None, remove=False, extra=False):
            def mutate(records):
                record = configuration_record()
                if remove:
                    del record["metadata"][field]
                elif extra:
                    record["metadata"]["retained_source"] = value
                elif field is None:
                    record["metadata"] = value
                else:
                    record["metadata"][field] = value
                insert_after_dispatch(records, [record])
            return mutate

        cases = {
            "empty": (invalid_provenance({}), "invalid configuration update"),
            "missing-client": (
                invalid_provenance(None, "client_authored", remove=True),
                "unknown record metadata",
            ),
            "missing-harness": (
                invalid_provenance(None, "harness_authored_configuration", remove=True),
                "invalid configuration update",
            ),
            "client-none": (
                invalid_provenance(None, "client_authored"), "unknown record metadata"
            ),
            "client-true": (
                invalid_provenance(True, "client_authored"), "unknown record metadata"
            ),
            "client-zero": (
                invalid_provenance(0, "client_authored"), "unknown record metadata"
            ),
            "client-one": (
                invalid_provenance(1, "client_authored"), "unknown record metadata"
            ),
            "harness-none": (
                invalid_provenance(None, "harness_authored_configuration"),
                "unknown record metadata",
            ),
            "harness-false": (
                invalid_provenance(False, "harness_authored_configuration"),
                "unknown record metadata",
            ),
            "harness-zero": (
                invalid_provenance(0, "harness_authored_configuration"),
                "unknown record metadata",
            ),
            "harness-one": (
                invalid_provenance(1, "harness_authored_configuration"),
                "unknown record metadata",
            ),
            "extra": (
                invalid_provenance("extra", extra=True), "unknown record metadata"
            ),
            "metadata-none": (invalid_provenance(None), "unknown record metadata"),
        }
        for name in sorted(cases):
            mutate, reason = cases[name]
            with self.subTest(name=name):
                # A null metadata object cannot carry sequence fields; test the
                # same invalid object in both modes after sequence assignment.
                if name == "metadata-none":
                    def null_metadata(records):
                        find_record(
                            records, "response_item", "configuration_update"
                        )["metadata"] = None

                    self.assert_pair(
                        "configuration-" + name,
                        mutate=with_configuration,
                        options={"after_sequence": null_metadata},
                        status=2, reason=reason,
                    )
                else:
                    self.assert_pair(
                        "configuration-" + name, mutate=mutate,
                        status=2 if reason == "unknown record metadata" else 1,
                        reason=reason,
                    )

    def test_invalid_sequence_metadata(self):
        def change_field(index, field, value):
            def apply(records):
                response_items(records)[index]["metadata"][field] = value
            return apply

        def remove_field(index, field):
            def apply(records):
                del response_items(records)[index]["metadata"][field]
            return apply

        def remove_pair(index):
            def apply(records):
                metadata = response_items(records)[index]["metadata"]
                for key in SEQUENCE_KEYS:
                    del metadata[key]
            return apply

        cases = {
            "missing-history": (
                remove_field(0, "history_sequence"), "incomplete sequence metadata"
            ),
            "missing-sampled": (
                remove_field(0, "sampled_through_sequence"),
                "incomplete sequence metadata",
            ),
            "mixed-first-legacy": (remove_pair(0), "mixed sequence metadata"),
            "mixed-later-legacy": (remove_pair(1), "mixed sequence metadata"),
            "sampled-over-history": (
                change_field(0, "sampled_through_sequence", 1),
                "invalid sequence metadata",
            ),
            "duplicate-history": (
                change_field(1, "history_sequence", 0), "invalid sequence metadata"
            ),
            "reversed-history": (
                change_field(1, "history_sequence", -1), "invalid sequence metadata"
            ),
            "gapped-history": (
                change_field(1, "history_sequence", 2), "invalid sequence metadata"
            ),
        }

        def decreasing_sampled(records):
            items = response_items(records)
            items[1]["metadata"]["sampled_through_sequence"] = 1
            items[2]["metadata"]["sampled_through_sequence"] = 0

        cases["decreasing-sampled"] = (
            decreasing_sampled, "invalid sequence metadata"
        )
        for field in sorted(SEQUENCE_KEYS):
            for label, value in (
                ("bool", True), ("bool-false", False), ("float", 0.0), ("string", "0"),
                ("negative", -1), ("null", None), ("list", []), ("dict", {}),
            ):
                cases[field + "-" + label] = (
                    change_field(0, field, value), "invalid sequence metadata"
                )

        def third_unknown(records):
            response_items(records)[0]["metadata"]["unexpected"] = False

        cases["third-unknown"] = (third_unknown, "unknown record metadata")

        def nonresponse(values):
            def apply(records):
                record = find_record(records, "event_msg", "task_started")
                record["metadata"] = values
            return apply

        cases["nonresponse-pair"] = (
            nonresponse({"history_sequence": 0, "sampled_through_sequence": 0}),
            "sequence metadata on non-response item",
        )
        cases["nonresponse-single"] = (
            nonresponse({"history_sequence": 0}),
            "sequence metadata on non-response item",
        )
        for label, value in (("list", []), ("null", None)):
            def invalid_object(records, value=value):
                response_items(records)[0]["metadata"] = value
            cases["metadata-" + label] = (invalid_object, "unknown record metadata")

        for name in sorted(cases):
            mutation, reason = cases[name]
            with self.subTest(name=name):
                result = self.invoke(
                    "sequence-invalid-" + name, self.base_factory, True,
                    options={"after_sequence": mutation},
                )
                self.assert_result(result, 2, reason)

    def test_first_pass_precedes_role_validation(self):
        def identity_fault(records):
            records[0]["payload"]["id"] = "wrong-thread"

        def malformed_metadata(records):
            response_items(records)[-1]["metadata"]["history_sequence"] = True

        result = self.invoke(
            "first-pass-before-identity", self.base_factory, True,
            mutate=identity_fault, options={"after_sequence": malformed_metadata},
        )
        self.assert_result(result, 2, "invalid sequence metadata")

        def schema_fault(records):
            records[-1]["payload"] = []

        result = self.invoke(
            "first-pass-schema", self.base_factory, True, mutate=schema_fault,
        )
        self.assert_result(result, 2, "invalid record schema")

    def test_deferred_namespace_declaration(self):
        def deferred(records):
            insert_after_dispatch(records, legacy.deferred_namespace_fixture())

        self.assert_pair("deferred-valid", mutate=deferred, status=0)

        def extra_known_metadata(records):
            declaration = next(
                record for record in records
                if record["type"] == "response_item"
                and record["payload"].get("id") == "deferred-namespace-fixture"
            )
            declaration.setdefault("metadata", {})["client_authored"] = False

        self.assert_pair(
            "deferred-extra-known", mutate=deferred,
            options={"after_sequence": extra_known_metadata},
            status=1, reason="invalid deferred namespace declaration",
        )

    def test_identity_and_lifecycle_faults(self):
        def set_nested(record_type, payload_type, path, value):
            def mutate(records):
                target = find_record(records, record_type, payload_type)["payload"]
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
            return mutate

        def outgoing(records):
            dispatch = find_record(records, "response_item", "agent_message")
            forward = copy.deepcopy(dispatch)
            forward["payload"]["author"] = legacy.AGENT
            forward["payload"]["recipient"] = "/root/other"
            insert_after_dispatch(records, [forward])

        def extra_tool(records):
            insert_after_dispatch(records, [{
                "timestamp": "2026-01-01T00:00:00Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call", "name": "extra",
                    "call_id": "extra-call", "input": "x", "status": "completed",
                },
            }])

        def missing_terminal(records):
            records.pop()

        def repeated_terminal(records):
            records.append(copy.deepcopy(records[-1]))

        cases = {
            "thread": (
                set_nested("session_meta", None, ["id"], "wrong"),
                1, "session identity mismatch", None,
            ),
            "parent": (
                set_nested("session_meta", None, ["parent_thread_id"], "wrong"),
                1, "session identity mismatch", None,
            ),
            "cwd": (
                set_nested("session_meta", None, ["cwd"], "/wrong"),
                1, "session identity mismatch", None,
            ),
            "agent": (
                set_nested("session_meta", None, ["agent_path"], "/root/other"),
                1, "session identity mismatch", None,
            ),
            "model": (
                set_nested("turn_context", None, ["model"], "wrong"),
                1, "turn context mismatch", None,
            ),
            "effort": (
                set_nested("turn_context", None, ["effort"], "wrong"),
                1, "turn context mismatch", None,
            ),
            "tier": (
                set_nested(
                    "event_msg", "thread_settings_applied",
                    ["thread_settings", "service_tier"], "wrong",
                ),
                1, "thread settings mismatch", None,
            ),
            "start": (
                set_nested("event_msg", "task_started", ["turn_id"], "wrong"),
                1, "invalid task start", None,
            ),
            "terminal-content": (
                set_nested(
                    "event_msg", "task_complete", ["last_agent_message"], "wrong"
                ),
                1, "uncorrelated task terminal", None,
            ),
            "terminal-missing": (
                missing_terminal, 1, "missing or repeated lifecycle record", None,
            ),
            "terminal-repeated": (
                repeated_terminal, 1, "record after terminal", None,
            ),
            "forward": (
                outgoing, 1, "unexpected inter-agent message", 1,
            ),
            "extra-tool": (
                extra_tool, 1, "unknown or effectful record: response_item/custom_tool_call",
                None,
            ),
        }
        for name in sorted(cases):
            mutate, status, reason, forwarded = cases[name]
            with self.subTest(name=name):
                self.assert_pair(
                    "fault-" + name, mutate=mutate, status=status,
                    reason=reason, forwarded=forwarded,
                )

        self.assert_pair(
            "fault-digest", options={"sha256": "0" * 64},
            status=2, reason="digest mismatch",
        )
        self.assert_pair(
            "fault-startup", options={"startup_sha256": "0" * 64},
            status=2,
            reason="initial inputs differ from independently anchored host startup",
        )

    def test_reader_faults(self):
        def reader_call(records):
            return find_record(records, "response_item", "custom_tool_call")["payload"]

        def reader_output(records):
            return find_record(
                records, "response_item", "custom_tool_call_output"
            )["payload"]

        def reader_effect(records):
            return next(
                record["payload"]["item"] for record in records
                if record["type"] == "event_msg"
                and record["payload"].get("type") == "item_completed"
                and record["payload"].get("item", {}).get("type") == "CommandExecution"
            )

        def bad_source(records):
            reader_call(records)["input"] += " "

        def bad_output(records):
            reader_output(records)["output"][1]["text"] = "wrong"

        def bad_correlation(records):
            reader_output(records)["call_id"] = "wrong"

        def bad_child_exit(records):
            reader_effect(records)["exit_code"] = 1

        cases = {
            "source": (bad_source, "unexpected reader call"),
            "output": (bad_output, "reader output mismatch"),
            "correlation": (bad_correlation, "reader output mismatch"),
            "child-exit": (bad_child_exit, "uncorrelated reader effect"),
        }
        for name in sorted(cases):
            mutate, reason = cases[name]
            with self.subTest(name=name):
                self.assert_pair(
                    "reader-fault-" + name, factory=self.reader_factory,
                    mutate=mutate, options={"reader": True}, reason=reason,
                )

        for name, options, reason in (
            (
                "packet-digest",
                {"reader": True, "packet_sha256": "0" * 64},
                "packet digest mismatch",
            ),
            (
                "forwarding-allowed",
                {"reader": True, "allow_forwarding": True},
                "sealed packet, pinned startup, zero writers and no forwarding required",
            ),
            (
                "write-root",
                {"reader": True, "write_root": "/work"},
                "sealed packet, pinned startup, zero writers and no forwarding required",
            ),
            (
                "startup-missing",
                {"reader": True, "omit_startup": True},
                "sealed packet, pinned startup, zero writers and no forwarding required",
            ),
        ):
            with self.subTest(name=name):
                self.assert_pair(
                    "reader-fault-" + name, factory=self.reader_factory,
                    options=options, status=2, reason=reason,
                )


    def test_native_envelope_additive_fields(self):
        def settings(records):
            return find_record(records, "event_msg", "thread_settings_applied")["payload"]["thread_settings"]

        def completed(records, item_type="AgentMessage"):
            return next(
                record["payload"] for record in records
                if record["type"] == "event_msg"
                and record["payload"].get("type") == "item_completed"
                and record["payload"]["item"].get("type") == item_type
            )

        def requested(value):
            return lambda records: settings(records).__setitem__("requested_approvals_reviewer", value)

        def count(value, item_type="AgentMessage"):
            return lambda records: completed(records, item_type).__setitem__("content_token_count", value)

        def combined(records):
            requested("auto_review")(records)
            count(129)(records)

        self.assert_pair("requested-auto-review", mutate=requested("auto_review"), status=0)
        for value in (0, 129):
            self.assert_pair("content-count-" + str(value), mutate=count(value), status=0)
        self.assert_pair("combined-envelope-fields", mutate=combined, status=0)
        self.assert_pair(
            "reader-envelope-fields", factory=self.reader_factory, mutate=combined,
            options={"reader": True}, status=0,
        )
        for name, value in (("other", "other"), ("none", None), ("bool", True)):
            self.assert_pair(
                "requested-invalid-" + name, mutate=requested(value),
                status=1, reason="thread settings mismatch",
            )
        for name, value in (
            ("true", True), ("false", False), ("negative", -1),
            ("string", "0"), ("float", 0.0), ("none", None),
        ):
            self.assert_pair(
                "content-count-invalid-" + name, mutate=count(value),
                status=1, reason="invalid content token count",
            )
        self.assert_pair(
            "content-count-command", factory=self.reader_factory,
            mutate=count(0, "CommandExecution"), options={"reader": True},
            status=1, reason="invalid content token count",
        )
        self.assert_pair(
            "unknown-thread-setting",
            mutate=lambda records: settings(records).__setitem__("unknown_setting", True),
            status=1, reason="thread settings mismatch",
        )


if __name__ == "__main__":
    unittest.main()
