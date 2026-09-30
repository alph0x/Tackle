"""Execute the installed Markdown recipe; fixtures contain original history bytes."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)

GUIDE = INSTALL / "references/guides/context-lifecycle.md"


def recipe():
    namespace = {}
    code = GUIDE.read_text().split("```python\n", 1)[1].split("\n```", 1)[0]
    exec(compile(code, str(GUIDE), "exec"), namespace)
    return namespace


def fixture(root, count=10):
    sources = ["task-board.md", "decisions.md", "questions.md", "contract.md", "tasks/T-A.md"]
    for name, body in zip(sources, [
        "Schema: tackle-workspace/5\n\nT-A: Checking; failure F-old; cycles spent: 2/3\n",
        "D-01 (still binding): preserve customers' original bytes.\n",
        "No pending decisions.\n", "RA: preserve bytes, including CRLF.\n",
        "T-A consumes RA; only declared files may change.\n",
    ]):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    entries = [f"## 2026-09-01 · session {n} · task {n}\n\n".encode() +
               (b"Failed F-old; spent cycles: 2/3; unresolved.\r\n" if n == 1 else
                b"Completed task.\n") + b"Original detail: " + b"x" * 1024 + b"\n"
               for n in range(1, count + 1)]
    (root / "history.md").write_bytes(b"# History\n\n" + b"".join(entries))
    return sources, entries


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sources, self.original = fixture(self.root)
        self.api = recipe()
        self.context = self.api["Context"](self.root)
        self.scope = {"tasks": ["T-A"], "requirements": ["RA"], "milestone": "M1"}

    def projection(self):
        return self.context.project(self.scope, self.sources)

    def test_workspace_projects_and_exports_current_names(self):
        self.projection()
        self.assertTrue((self.root / "current-work.md").is_file())
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "handoff"
            self.context.export(self.scope, self.sources, destination, event_numbers=[1])
            self.assertTrue((destination / "handoff-brief.md").is_file())
            self.assertEqual(self.api["Context"].verify_export(destination)["projection"]["last_event"], 10)

    def test_an_older_workspace_path_is_refused(self):
        for older in ("board.md", "log.md", "log-archive.md", "coordinator.md", "HANDOFF.md"):
            with self.subTest(path=older):
                (self.root / older).write_text("# Older\n")
                with self.assertRaisesRegex(ValueError, "migrate first: older workspace path " + older):
                    self.api["Context"](self.root)
                (self.root / older).unlink()

    def test_a_board_below_5_or_with_crlf_endings_is_refused_before_any_write(self):
        for body in (b"Schema: tackle-workspace/4\n\nT-A: Checking\n", b"T-A: Checking\n",
                     b"Schema: tackle-workspace/5\r\n\r\nT-A: Checking\r\n"):
            with self.subTest(body=body):
                (self.root / "task-board.md").write_bytes(body)
                before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
                with self.assertRaisesRegex(ValueError, "migrate first: task-board.md has no tackle-workspace/5"):
                    self.api["Context"](self.root).project(self.scope, self.sources)
                self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()})

    def test_a_current_focused_workspace_is_not_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "plan.md").write_text("Gate: Lite\n# Task\n")
            (root / "resource-usage.md").write_text("# Resource usage\n")
            (root / "history.md").write_bytes(b"# History\n\n" + self.original[0])
            context = self.api["Context"](root)
            self.assertEqual(context.history(), b"# History\n\n" + self.original[0])

    def test_projection_is_verified_and_status_is_read_only(self):
        self.projection()
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = self.context.current(self.scope, self.sources)
        self.assertIn("D-01 (still binding)", result["sources"]["decisions.md"])
        self.assertEqual(result["last_event"], 10)
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_contract_change_rejects_stale_checkpoint(self):
        self.projection()
        (self.root / "contract.md").write_text("RA changed materially.\n")
        with self.assertRaisesRegex(ValueError, "stale"):
            self.context.current(self.scope, self.sources)

    def test_membership_and_semantic_scope_are_part_of_revision(self):
        self.projection()
        for sources, scope in [(self.sources[:-1], self.scope),
                               (self.sources, dict(self.scope, tasks=["P-02"]))]:
            with self.assertRaisesRegex(ValueError, "stale"):
                self.context.current(scope, sources)

    def test_new_event_reopened_task_and_new_blocker_invalidate(self):
        for path, value in [("task-board.md", "T-A reopened\n"),
                            ("questions.md", "Q-03: blocked on product decision\n"),
                            ("history.md", "## 2026-09-02 · session 11 · interrupted\n")]:
            self.projection()
            with (self.root / path).open("a") as stream:
                stream.write(value)
            with self.assertRaisesRegex(ValueError, "stale"):
                self.context.current(self.scope, self.sources)

    def test_archive_preserves_original_bytes_order_and_failure_lineage(self):
        before = (self.root / "history.md").read_bytes()
        self.context.archive(keep=5, segment_bytes=2500)
        self.assertEqual(self.context.history(), before)
        self.assertEqual(self.context.event(1), self.original[0])
        self.assertIn(b"spent cycles: 2/3", self.context.event(1))
        self.assertEqual(len(self.context.events((self.root / "history.md").read_bytes())[1]), 5)
        self.projection()
        self.assertIn("still binding", self.context.current(self.scope, self.sources)["sources"]["decisions.md"])

    def test_missing_segment_is_visible_even_for_routine_resume(self):
        self.context.archive()
        self.projection()
        next((self.root / "history").glob("segment-*.md")).unlink()
        with self.assertRaisesRegex(ValueError, "missing archive"):
            self.context.current(self.scope, self.sources)

    def test_corrupt_archive_never_becomes_evidence(self):
        self.context.archive()
        path = next((self.root / "history").glob("segment-*.md"))
        path.chmod(0o644)
        path.write_bytes(path.read_bytes().replace(b"Failed", b"Passed"))
        with self.assertRaisesRegex(ValueError, "corrupt archive"):
            self.context.event(1)

    def test_rotation_recovers_every_publish_boundary_without_duplicate_events(self):
        for phase in ["segment", "journal", "index", "log"]:
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                fixture(root)
                before = (root / "history.md").read_bytes()
                context = self.api["Context"](root)
                with self.assertRaisesRegex(RuntimeError, "injected interruption"):
                    context.archive(fail_after=phase)
                if phase != "segment":
                    with self.assertRaisesRegex(ValueError, "incomplete maintenance"):
                        context.project(self.scope, self.sources)
                context.recover()
                context.archive()
                self.assertEqual(context.history(), before)
                self.assertEqual(context.last_event(), 10)
                self.assertFalse(context.recover())

    def test_recovery_refuses_to_overwrite_uncoordinated_append(self):
        with self.assertRaises(RuntimeError):
            self.context.archive(fail_after="index")
        with (self.root / "history.md").open("ab") as stream:
            stream.write(b"\nUncoordinated append\n")
        before = (self.root / "history.md").read_bytes()
        with self.assertRaisesRegex(ValueError, "changed during maintenance"):
            self.context.recover()
        self.assertEqual((self.root / "history.md").read_bytes(), before)

    def test_single_writer_lock_covers_archive_and_projection(self):
        with self.context.writer():
            with self.assertRaisesRegex(ValueError, "writer active"):
                self.api["Context"](self.root).archive()
            with self.assertRaisesRegex(ValueError, "writer active"):
                self.api["Context"](self.root).project(self.scope, self.sources)

    def test_completion_interruption_does_not_repeat_side_effect(self):
        effect = self.root / "delivered.txt"
        effect.write_text("once")
        self.projection()
        (self.root / "task-board.md").write_text("T-A: Checking; completion update interrupted\n")
        with self.assertRaisesRegex(ValueError, "stale"):
            self.context.current(self.scope, self.sources)
        self.assertEqual(effect.read_text(), "once")
        self.projection()
        self.assertIn("Checking", self.context.current(self.scope, self.sources)["sources"]["task-board.md"])
        self.assertEqual(effect.read_text(), "once")

    def test_current_projection_cannot_be_tampered_into_success(self):
        self.projection()
        path = self.root / "current-work.md"
        path.write_text(path.read_text().replace("Checking", "Complete"))
        with self.assertRaisesRegex(ValueError, "projection source mismatch"):
            self.context.current(self.scope, self.sources)

    def test_export_survives_original_directory_removal(self):
        self.context.archive()
        self.projection()
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "handoff"
            self.context.export(self.scope, self.sources, destination, event_numbers=[1])
            shutil.rmtree(self.root)
            bundle = self.api["Context"].verify_export(destination)
            self.assertIn("still binding", bundle["projection"]["sources"]["decisions.md"])
            self.assertEqual((destination / "history/event-1.md").read_bytes(), self.original[0])
            (destination / "contract.md").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "export inventory"):
                self.api["Context"].verify_export(destination)

    def test_existing_archive_is_preserved_and_explicitly_adopted(self):
        original = "## 2026-08-01 · session 0 · earlier\nLegacy original\n".encode()
        (self.root / "history-archive.md").write_bytes(original)
        self.projection()
        self.assertEqual((self.root / "history-archive.md").read_bytes(), original)
        self.context.archive()
        self.assertTrue(self.context.history().endswith(b"".join(self.original)))
        self.assertEqual(self.context.event(1), original)
        self.assertEqual((self.root / "history-archive.md").read_bytes(), original)

    def test_invalid_archive_policy_and_path_escape_fail_without_source_change(self):
        before = (self.root / "history.md").read_bytes()
        for keep in [0, -1, True]:
            with self.assertRaises(ValueError):
                self.context.archive(keep=keep)
        for name in ["../outside.md", "/tmp/outside.md"]:
            with self.assertRaises(ValueError):
                self.context.project(self.scope, self.sources + [name])
        self.assertEqual((self.root / "history.md").read_bytes(), before)

    def test_original_heading_lookup_and_unknown_event(self):
        self.context.archive()
        self.assertEqual(self.context.lookup("## 2026-09-01 · session 1 · task 1"), self.original[0])
        with self.assertRaisesRegex(ValueError, "missing event"):
            self.context.event(99)

    def test_completion_event_retry_is_idempotent_and_wrong_head_blocks(self):
        projection = self.projection()
        data = b"## 2026-09-02 - session 11 - checked closure\nTask T-A Complete; record observed.\n"
        args = (data, projection["last_event"], projection["last_event_revision"])
        self.assertTrue(self.context.append_event(*args))
        self.assertFalse(self.context.append_event(*args))
        self.assertEqual(self.context.last_event(), 11)
        with self.assertRaisesRegex(ValueError, "head changed"):
            self.context.append_event(data + b"different\n", 10, projection["last_event_revision"])

    def test_pending_transaction_cannot_drop_an_original(self):
        with self.assertRaises(RuntimeError):
            self.context.archive(keep=5, segment_bytes=2500, fail_after="index")
        path = self.root / "history/transaction.md"
        transaction = self.api["decode"](path.read_bytes())
        transaction["next_index"]["segments"].pop()
        path.write_bytes(self.api["document"]("Pending history maintenance", transaction))
        with self.assertRaises(ValueError):
            self.context.recover()
        self.assertEqual((self.root / "history.md").read_bytes(), b"# History\n\n" + b"".join(self.original))

    def test_out_of_order_archive_boundary_is_rejected(self):
        self.context.archive()
        path = self.root / "history.md"
        path.write_bytes(path.read_bytes().replace(b"2026-09-01", b"2026-08-01"))
        with self.assertRaisesRegex(ValueError, "history out of order"):
            self.projection()

    def test_abrupt_process_exit_releases_lock_and_recovers_originals(self):
        source = GUIDE.read_text().split("```python\n", 1)[1].split("\n```", 1)[0]
        child = source + "\nContext.stop = staticmethod(lambda requested, phase: os._exit(73) if phase == 'index' else None)\nContext(Path(sys.argv[1])).archive()\n"
        child = "import sys\n" + child
        result = subprocess.run([sys.executable, "-c", child, str(self.root)], capture_output=True)
        self.assertEqual(result.returncode, 73, result.stderr)
        self.assertTrue(self.context.recover())
        self.assertEqual(self.context.history(), b"# History\n\n" + b"".join(self.original))

    def test_failed_completion_event_publish_preserves_exact_old_event(self):
        projection = self.projection()
        original = (self.root / "history.md").read_bytes()
        event = b"## 2026-09-02 - session 11 - checked closure\nVerified result\n"
        with mock.patch.object(self.api["os"], "replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                self.context.append_event(event, 10, projection["last_event_revision"])
        self.assertEqual((self.root / "history.md").read_bytes(), original)
        self.assertTrue(self.context.append_event(event, 10, projection["last_event_revision"]))

    def test_handoff_carries_checked_record_bundle_without_original_store(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp)
            for name, guide in [("capture", "full-checks.md"), ("lifecycle", "record-lifecycle.md")]:
                code = (INSTALL / "references/guides" / guide).read_text().split("```python\n", 1)[1].split("\n```", 1)[0]
                (runtime / (name + ".py")).write_text(code)
            (runtime / "initiative").mkdir()
            (runtime / "child.py").write_text("print('observed pass')\n")
            (runtime / "input.txt").write_text("required bytes\n")
            spec = {"workspace": "initiative", "argv": [sys.executable, "child.py"],
                    "selectors": [{"glob": "input.txt", "required": True}], "artifacts": [], "timeout_seconds": 2}
            (runtime / "spec.json").write_text(json.dumps(spec))
            child = subprocess.run([sys.executable, "capture.py", "spec.json"], cwd=runtime, capture_output=True, text=True)
            self.assertEqual(child.returncode, 0, child.stderr)
            record = Path(child.stdout.strip()).parent
            command = "import sys;from pathlib import Path;from lifecycle import export_records;export_records(Path(sys.argv[1]),[sys.argv[2]],Path(sys.argv[3]))"
            exported = runtime / "checked-records"
            child = subprocess.run([sys.executable, "-c", command, str(record.parent), record.name, str(exported)],
                                   cwd=runtime, capture_output=True, text=True)
            self.assertEqual(child.returncode, 0, child.stderr)
            with (self.root / "task-board.md").open("a") as stream:
                stream.write("Required record: evidence/" + record.name + "/result.json\n")
            self.projection()
            handoff = runtime / "handoff"
            self.context.export(self.scope, self.sources, handoff, record_bundles={"evidence": exported})
            shutil.rmtree(record.parent)
            shutil.rmtree(exported)
            self.api["Context"].verify_export(handoff)
            command = "import sys;from pathlib import Path;from lifecycle import verify_bundle;from capture import read_record;verify_bundle(Path(sys.argv[1]));read_record(Path(sys.argv[1])/sys.argv[2],require_pass=True)"
            checked = subprocess.run([sys.executable, "-c", command, str(handoff / "evidence"), record.name],
                                     cwd=runtime, capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_portable_record_alias_cannot_escape_export_scope(self):
        self.projection()
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            exported = directory / "records"
            exported.mkdir()
            outside = directory / "unrelated"
            outside.write_text("private sentinel")
            (exported / "stdout.bin").symlink_to("../unrelated")
            with self.assertRaisesRegex(ValueError, "unsafe record alias"):
                self.context.export(self.scope, self.sources, directory / "handoff",
                                    record_bundles={"evidence": exported})
            self.assertEqual(outside.read_text(), "private sentinel")

    def test_handoff_holds_one_source_revision_boundary(self):
        projection = self.projection()
        original_current = self.context.current
        event = b"## 2026-09-02 - session 11 - later state\nLater task changes\n"
        writer = self.api["Context"](self.root)
        def current_with_competing_writer(scope, sources):
            current = original_current(scope, sources)
            with self.assertRaisesRegex(ValueError, "writer active"):
                writer.append_event(event, projection["last_event"], projection["last_event_revision"])
            return current
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(self.context, "current", current_with_competing_writer):
                self.context.export(self.scope, self.sources, Path(temp) / "handoff", event_numbers=[10])
            with self.assertRaisesRegex(ValueError, "outside checkpoint"):
                self.context.export(self.scope, self.sources, Path(temp) / "later", event_numbers=[11])
            def current_with_external_change(scope, sources):
                current = original_current(scope, sources)
                (self.root / "task-board.md").write_text("T-A reopened by source owner\n")
                return current
            with mock.patch.object(self.context, "current", current_with_external_change):
                with self.assertRaisesRegex(ValueError, "sources changed during handoff"):
                    self.context.export(self.scope, self.sources, Path(temp) / "changed")

    def test_export_rejects_inconsistent_projection_text_even_with_valid_inventory(self):
        self.projection()
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "handoff"
            self.context.export(self.scope, self.sources, destination)
            bundle = self.api["Context"](destination)
            value = self.api["decode"]((destination / "handoff-brief.md").read_bytes())
            value["sources"]["task-board.md"] = "T-A Complete (invented)"
            bundle.write("handoff-brief.md", self.api["document"]("Portable current work", value))
            bundle.write("inventory.md", self.api["document"]("Handoff inventory", bundle.file_inventory()))
            with self.assertRaisesRegex(ValueError, "source text/revision mismatch"):
                self.api["Context"].verify_export(destination)


if __name__ == "__main__":
    unittest.main()
