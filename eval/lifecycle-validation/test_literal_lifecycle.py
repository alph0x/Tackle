"""Execute the shipped Markdown validator against independent lifecycle cases."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HEADER = "| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |\n"
LEGACY = "| Point | Role | Tier | Model | Effort | Tokens in | Tokens out | Session |\n|---|---|---|---|---|---|---|---|\n| P-01 | Driver | standard | model | high | n/a | n/a | old-session |\n"


def event(kind="start", *, run="run-1", point="P-01", role="Driver", attempts="n/a", rework="n/a"):
    return f"| {run} | {kind} | {point} | {role} | harness | standard | model | n/a | n/a | observed | {attempts} | {rework} | n/a | fixture |\n"


def check(body):
    line = next(row for row in (ROOT / "references/guides/lint-spec.md").read_text().splitlines()
                if row.startswith("| 16 ·"))
    command = line.split(" | `", 1)[1].rsplit("` |", 1)[0].replace("<slug>", "case")
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory) / "docs/plans/case"
        workspace.mkdir(parents=True)
        (workspace / "usage.md").write_text(body)
        return subprocess.run(["sh", "-c", command], cwd=directory, capture_output=True, text=True, timeout=5)


class LifecycleCompatibility(unittest.TestCase):
    def assert_valid(self, body):
        result = check(body)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def assert_invalid(self, body, diagnostic):
        result = check(body)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertIn(diagnostic, result.stdout)

    def test_unknown_counts_remain_valid(self):
        self.assert_valid(HEADER + event() + event("finish"))

    def test_legacy_then_v2_preserves_unknowns(self):
        self.assert_valid(LEGACY + "\nSchema: tackle-observability/2\n" + HEADER + event() + event("observe-incomplete"))

    def test_legacy_only_remains_readable(self):
        self.assert_valid(LEGACY)

    def test_known_zero_and_positive_counts(self):
        self.assert_valid(HEADER + event(attempts="0", rework="0") + event("finish", attempts="2", rework="1"))

    def test_empty_negative_and_nonnumeric_counts_still_fail(self):
        for count in ("", "-1", "unknown", "1.5", "1x"):
            for field in ("attempts", "rework"):
                with self.subTest(count=count, field=field):
                    self.assert_invalid(HEADER + event(**{field: count}), "Attempts/Rework")

    def test_orphan_terminal_after_legacy_still_fails(self):
        self.assert_invalid(LEGACY + HEADER + event("finish"), "terminal before start")

    def test_late_start_does_not_repair_history(self):
        self.assert_invalid(HEADER + event("finish") + event(), "terminal before start")

    def test_duplicates_and_role_mismatch_still_fail(self):
        for body, message in ((event() + event(), "duplicate start"),
                              (event() + event("finish") + event("observe-incomplete"), "duplicate terminal"),
                              (event() + event("finish", role="Checker"), "Point/Role changed")):
            with self.subTest(message=message):
                self.assert_invalid(HEADER + body, message)

    def test_legacy_header_after_v2_cannot_hide_bad_events(self):
        self.assert_invalid(HEADER + event() + LEGACY + event("finish", run="orphan"), "terminal before start")

    def test_truncated_and_unknown_event_still_fail(self):
        self.assert_invalid(LEGACY + HEADER + "| run-x | start | P-01 |\n", "malformed data row")
        self.assert_invalid(HEADER + event("checkpoint"), "unknown Event")


if __name__ == "__main__":
    unittest.main(verbosity=2)
