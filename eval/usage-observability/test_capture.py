import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "references/guides/codex-native-usage.md"


def recipe():
    source = GUIDE.read_text()
    match = re.search(r"<!-- codex-usage-recipe:start -->\n```python\n(.*?)\n```\n<!-- codex-usage-recipe:end -->", source, re.S)
    if not match:
        raise AssertionError("literal Codex usage recipe missing")
    return match.group(1)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        (self.workspace / "usage.md").write_text("Schema: tackle-observability/2\n")
        self.trace = self.root / "events.jsonl"

    def write_events(self, *events):
        self.trace.write_text("".join(json.dumps(event) + "\n" for event in events))

    def run_recipe(self, trace=True, env=None):
        argv = [sys.executable, "-c", recipe(), str(self.workspace)]
        if trace:
            argv.append(str(self.trace))
        runtime = os.environ.copy()
        runtime.pop("CODEX_THREAD_ID", None)
        if env:
            runtime.update(env)
        return subprocess.run(argv, text=True, capture_output=True, env=runtime)

    def observations(self):
        return [json.loads(line) for line in (self.workspace / "usage.telemetry.jsonl").read_text().splitlines()]

    def test_desktop_uses_child_thread_and_exposes_turn_metadata_without_prompt(self):
        child = "11111111-1111-4111-8111-111111111111"
        parent = "22222222-2222-4222-8222-222222222222"
        turn = "33333333-3333-4333-8333-333333333333"
        self.write_events(
            {"timestamp": "2026-09-23T10:00:00Z", "type": "session_meta", "payload": {"id": child, "source": {"subagent": {"thread_spawn": {"parent_thread_id": parent}}}}},
            {"timestamp": "2026-09-23T10:00:00Z", "type": "session_meta", "payload": {"id": parent, "source": "vscode"}},
            {"timestamp": "2026-09-23T10:00:01Z", "type": "turn_context", "payload": {"turn_id": turn, "model": "gpt-6-astra", "effort": "ultra"}},
            {"timestamp": "2026-09-23T10:00:02Z", "type": "response_item", "payload": {"type": "message", "content": "SECRET PROMPT"}},
            {"timestamp": "2026-09-23T10:00:03Z", "type": "token_usage_record", "payload": {"thread_id": child, "session_id": parent, "turn_id": turn, "response_id": "resp-1", "thread_token_usage": {"input_tokens": 100, "cached_input_tokens": 40, "cache_write_input_tokens": 0, "output_tokens": 20, "reasoning_output_tokens": 5}, "turn_token_usage": {"input_tokens": 70, "cached_input_tokens": 30, "cache_write_input_tokens": 0, "output_tokens": 10, "reasoning_output_tokens": 2}}},
            {"timestamp": "2026-09-23T10:00:04Z", "type": "event_msg", "payload": {"type": "task_complete", "turn_id": turn}},
        )
        result = self.run_recipe(env={"CODEX_THREAD_ID": child})
        self.assertEqual(result.returncode, 0, result.stderr)
        records = self.observations()
        self.assertEqual(len(records), 2)
        self.assertEqual({record["scope_id"] for record in records}, {child, f"{child}/turn/{turn}"})
        self.assertTrue(all(record["scope"] == "session" and record["run_id"] == "n/a" for record in records))
        self.assertEqual({record["metrics"]["input_tokens"] for record in records}, {70, 100})
        self.assertTrue(all(record["provenance"]["model_configured"] == "gpt-6-astra" for record in records))
        self.assertTrue(all(record["provenance"]["effort_configured"] == "ultra" for record in records))
        self.assertTrue(all(record["provenance"]["terminal_event_at"] == "2026-09-23T10:00:04Z" for record in records))
        self.assertNotIn("SECRET PROMPT", (self.workspace / "usage.telemetry.jsonl").read_text() + result.stdout)

    def test_cli_records_each_completed_turn_without_assigning_role(self):
        self.write_events(
            {"type": "thread.started", "thread_id": "cli-thread"},
            {"type": "turn.completed", "usage": {"input_tokens": 12, "output_tokens": 3, "cached_input_tokens": 5, "reasoning_output_tokens": 1}},
            {"type": "turn.failed", "error": "omitted"},
            {"type": "turn.completed", "usage": {"input_tokens": 9, "output_tokens": 2}},
        )
        result = self.run_recipe()
        self.assertEqual(result.returncode, 0, result.stderr)
        records = self.observations()
        self.assertEqual(len(records), 2)
        self.assertEqual([r["metrics"]["input_tokens"] for r in records], [12, 9])
        self.assertEqual([r["scope_id"] for r in records], ["cli-thread/turn/1", "cli-thread/turn/2"])
        self.assertTrue(all(r["run_id"] == "n/a" for r in records))
        self.assertNotIn("cache_read_tokens", records[1]["metrics"])

    def test_desktop_preserves_latest_observation_for_each_native_turn(self):
        self.write_events(
            {"type": "turn_context", "payload": {"turn_id": "turn-1", "model": "gpt-6-sol", "effort": "low"}},
            {"type": "token_usage_record", "payload": {"thread_id": "thread-1", "turn_id": "turn-1", "thread_token_usage": {"input_tokens": 10}, "turn_token_usage": {"input_tokens": 10}}},
            {"type": "turn_context", "payload": {"turn_id": "turn-2", "model": "gpt-6-sol", "effort": "high"}},
            {"type": "token_usage_record", "payload": {"thread_id": "thread-1", "turn_id": "turn-2", "thread_token_usage": {"input_tokens": 24}, "turn_token_usage": {"input_tokens": 14}}},
        )
        result = self.run_recipe()
        self.assertEqual(result.returncode, 0, result.stderr)
        records = self.observations()
        self.assertEqual(len(records), 3)
        turns = {r["scope_id"]: r for r in records if r["collector"] == "codex-desktop/turn/1"}
        self.assertEqual(turns["thread-1/turn/turn-1"]["metrics"]["input_tokens"], 10)
        self.assertEqual(turns["thread-1/turn/turn-2"]["metrics"]["input_tokens"], 14)
        self.assertEqual(turns["thread-1/turn/turn-1"]["provenance"]["effort_configured"], "low")
        self.assertEqual(turns["thread-1/turn/turn-2"]["provenance"]["effort_configured"], "high")

    def test_duplicate_capture_is_idempotent_and_new_snapshot_appends(self):
        thread = "thread-1"
        base = {"timestamp": "2026-09-23T10:00:01Z", "type": "token_usage_record", "payload": {"thread_id": thread, "turn_id": "turn-1", "response_id": "resp-1", "thread_token_usage": {"input_tokens": 10}, "turn_token_usage": {"input_tokens": 10}}}
        self.write_events(base)
        self.assertEqual(self.run_recipe().returncode, 0)
        before = (self.workspace / "usage.telemetry.jsonl").read_bytes()
        self.assertEqual(self.run_recipe().returncode, 0)
        self.assertEqual((self.workspace / "usage.telemetry.jsonl").read_bytes(), before)
        newer = {"timestamp": "2026-09-23T10:00:02Z", "type": "token_usage_record", "payload": {"thread_id": thread, "turn_id": "turn-1", "response_id": "resp-2", "thread_token_usage": {"input_tokens": 20}, "turn_token_usage": {"input_tokens": 20}}}
        self.write_events(base, newer)
        self.assertEqual(self.run_recipe().returncode, 0)
        self.assertEqual(len(self.observations()), 4)

    def test_later_terminal_event_enriches_existing_usage_observation(self):
        usage = {"timestamp": "2026-09-23T10:00:01Z", "type": "token_usage_record", "payload": {"thread_id": "thread-1", "turn_id": "turn-1", "thread_token_usage": {"input_tokens": 10}, "turn_token_usage": {"input_tokens": 10}}}
        self.write_events(usage)
        self.assertEqual(self.run_recipe().returncode, 0)
        self.assertEqual(len(self.observations()), 2)
        terminal = {"timestamp": "2026-09-23T10:00:02Z", "type": "event_msg", "payload": {"type": "task_complete", "turn_id": "turn-1"}}
        self.write_events(usage, terminal)
        self.assertEqual(self.run_recipe().returncode, 0)
        records = self.observations()
        self.assertEqual(len(records), 4)
        self.assertTrue(all(r["provenance"]["terminal_event_at"] == "2026-09-23T10:00:02Z" for r in records[-2:]))
        self.assertEqual(self.run_recipe().returncode, 0)
        self.assertEqual(len(self.observations()), 4)

    def test_invalid_or_missing_trace_never_writes_sidecar(self):
        self.write_events({"type": "token_usage_record", "payload": {"thread_id": "t", "turn_id": "u", "thread_token_usage": {"input_tokens": -1}, "turn_token_usage": {"input_tokens": -1}}})
        self.assertNotEqual(self.run_recipe().returncode, 0)
        self.assertFalse((self.workspace / "usage.telemetry.jsonl").exists())
        self.trace.write_text("{bad json\n")
        self.assertNotEqual(self.run_recipe().returncode, 0)
        self.assertFalse((self.workspace / "usage.telemetry.jsonl").exists())
        self.trace.unlink()
        self.assertNotEqual(self.run_recipe().returncode, 0)
        self.assertFalse((self.workspace / "usage.telemetry.jsonl").exists())

    def test_existing_malformed_sidecar_and_symlink_are_rejected(self):
        self.write_events({"type": "thread.started", "thread_id": "t"}, {"type": "turn.completed", "usage": {"input_tokens": 1}})
        sidecar = self.workspace / "usage.telemetry.jsonl"
        sidecar.write_text("not json\n")
        self.assertNotEqual(self.run_recipe().returncode, 0)
        self.assertEqual(sidecar.read_text(), "not json\n")
        sidecar.unlink()
        target = self.root / "protected"
        target.write_text("keep")
        sidecar.symlink_to(target)
        self.assertNotEqual(self.run_recipe().returncode, 0)
        self.assertEqual(target.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
