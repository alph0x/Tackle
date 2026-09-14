"""P-02 contract and literal lint-row fixtures.

These tests execute the commands copied from lint-spec.md against disposable workspace trees.
They do not run an installed Tackle engine or change product files.
"""
import hashlib
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINT = (ROOT.parent.parent / "references/guides/lint-spec.md").read_text()


def literal_row(number):
    line = next(line for line in LINT.splitlines() if line.startswith(f"| {number} ·"))
    return line.split(" | `", 1)[1].rsplit("` |", 1)[0]


def run_row(number, fixture, *, usage_dir=False):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        workspace = root / "docs/plans/demo"
        workspace.mkdir(parents=True)
        source = ROOT / "fixtures/contracts" / fixture
        for item in source.iterdir():
            if item.is_file():
                shutil.copyfile(item, workspace / item.name)
        completed = subprocess.run(
            ["sh", "-c", literal_row(number).replace("<slug>", "demo")],
            cwd=root, capture_output=True, text=True, timeout=5,
        )
        return completed


def run_row12(fixture):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        points = root / "docs/plans/demo/points"
        points.mkdir(parents=True)
        shutil.copyfile(ROOT / "fixtures/contracts" / fixture / "point.md",
                        points / "P-01.md")
        return subprocess.run(["sh", "-c", literal_row(12).replace("<slug>", "demo")],
                              cwd=root, capture_output=True, text=True, timeout=5)


def structural_contract_shape(text):
    """Check shape only; semantic completeness belongs to the independent review rubric."""
    return all(section in text for section in [
        "## Purpose and scope", "## Contract and cases", "## Approach",
        "## Acceptance and recovery",
    ]) and "### Case matrix" in text and "### Shared clauses (compiled)" in text


def run_generated_acceptance(point_path, *, valid, pretty=False, missing_json=False):
    command = point_path.read_text().split("```sh\n", 1)[1].split("\n```", 1)[0]
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        if valid:
            (root / "result.csv").write_bytes(b"name,score\nBo,3\nAda,2\n")
            result = '{"score": 3, "name": "Bo"}\n' if not pretty else '{\n  "name": "Bo",\n  "score": 3\n}\n'
            if not missing_json:
                (root / "result.json").write_text(result)
        else:
            (root / "result.csv").write_bytes(b"name,score\nAda,2\nBo,3\n")
            if not missing_json:
                (root / "result.json").write_text('{"score": 3, "name": "Bo"}\n')
        return subprocess.run(["sh", "-c", command], cwd=root,
                              capture_output=True, text=True, timeout=5)


def run_generated_unit_tests():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        fixture = ROOT / "fixtures/contracts/point"
        for name in ["normalize.py", "test_normalize.py"]:
            shutil.copyfile(fixture / name, root / name)
        return subprocess.run(["python3", "-m", "unittest", "-v", "test_normalize.py"],
                              cwd=root, capture_output=True, text=True, timeout=5)


def effort_declaration(text):
    lines = [line for line in text.splitlines() if line.startswith("- **Effort**: ")]
    if len(lines) != 1:
        return None
    return lines[0].split(": ", 1)[1].strip()


def validate_compiled_clause(point_path):
    text = point_path.read_text()
    metadata = re.search(
        r"\*\*Id\*\*: `([^`]+)` · \*\*revision\*\*: `([^`]+)` · "
        r"\*\*source\*\*: `([^`]+)` · \*\*sha256\*\*: `([0-9a-f]{64})`", text)
    block = re.search(r"<!-- CLAUSE-BYTES: [^\n]+ -->\n```text\n(.*?)\n```\n<!-- END-CLAUSE-BYTES -->", text, re.S)
    if not metadata or not block:
        return False
    clause_id, revision, source_name, digest = metadata.groups()
    source = point_path.parent / source_name
    try:
        source_bytes = source.read_bytes()
    except OSError:
        return False
    inline_bytes = (block.group(1) + "\n").encode("utf-8")
    first_line = source_bytes.splitlines()[0].decode("utf-8")
    return (source_name == "canonical-clause.md" and revision == "1"
            and first_line == f"Clause {clause_id} revision {revision}"
            and inline_bytes == source_bytes
            and hashlib.sha256(source_bytes).hexdigest() == digest)


class Contracts(unittest.TestCase):
    def test_templates_compile_coherent_point_and_expose_omission_for_review(self):
        complete = (ROOT / "fixtures/contracts/point/complete.md").read_text()
        omitted = (ROOT / "fixtures/contracts/point/omitted-requirement.md").read_text()
        keyword_only = (ROOT / "fixtures/contracts/point/keyword-only.md").read_text()
        self.assertTrue(structural_contract_shape(complete))
        self.assertTrue(structural_contract_shape(omitted))
        self.assertFalse(structural_contract_shape(keyword_only))
        complete_path = ROOT / "fixtures/contracts/point/complete.md"
        valid = run_generated_acceptance(complete_path, valid=True)
        pretty = run_generated_acceptance(complete_path, valid=True, pretty=True)
        invalid = run_generated_acceptance(complete_path, valid=False)
        missing_json = run_generated_acceptance(complete_path, valid=True, missing_json=True)
        self.assertEqual(valid.returncode, 0)
        self.assertEqual(valid.stdout, "PASS point\n")
        self.assertEqual(pretty.returncode, 0)
        self.assertEqual(pretty.stdout, "PASS point\n")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertNotIn("PASS point", invalid.stdout)
        self.assertNotEqual(missing_json.returncode, 0)
        self.assertNotIn("PASS point", missing_json.stdout)
        unit = run_generated_unit_tests()
        self.assertEqual(unit.returncode, 0)

    def test_template_has_compiled_contract_and_no_external_worker_prerequisite(self):
        template = (ROOT.parent.parent / "references/point.tmpl.md").read_text()
        for section in ["Purpose and scope", "Contract and cases", "Approach", "Acceptance and recovery"]:
            self.assertIn(section, template)
        self.assertIn("file alone", template)
        self.assertIn("clause id", template)
        self.assertIn("sha256", template)
        self.assertIn("valid semantic equivalents", template)
        self.assertIn("discovery", template)
        self.assertIn("experiment", template)
        self.assertEqual(effort_declaration(template), "{{resolved concrete value}}.")
        invalid_effort = (ROOT / "fixtures/contracts/point/effort-invalid.md").read_text()
        self.assertNotIn(effort_declaration(invalid_effort), {"inherit", "low", "medium", "high", "max"})
        for number in [6, 11, 16]:
            self.assertNotIn("|", literal_row(number))
        valid_effort = run_row12("row12/valid")
        invalid_effort_row = run_row12("row12/invalid")
        self.assertEqual(valid_effort.returncode, 0)
        self.assertEqual(valid_effort.stdout, "")
        self.assertEqual(invalid_effort_row.returncode, 0)
        self.assertIn("heroic", invalid_effort_row.stdout)

    def test_generated_clause_identity_accepts_exact_bytes_and_rejects_tamper(self):
        source = ROOT / "fixtures/contracts/point/canonical-clause.md"
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        point_path = ROOT / "fixtures/contracts/point/complete.md"
        point = point_path.read_text()
        self.assertIn(f"**sha256**: `{digest}`", point)
        self.assertTrue(validate_compiled_clause(point_path))
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            copied_point = directory / "complete.md"
            copied_source = directory / "canonical-clause.md"
            copied_point.write_text(point)
            copied_source.write_bytes(source.read_bytes())
            self.assertTrue(validate_compiled_clause(copied_point))
            copied_point.write_text(point.replace("acceptance evidence.", "tampered evidence.", 1))
            self.assertFalse(validate_compiled_clause(copied_point))
            copied_point.write_text(point)
            copied_source.write_bytes(source.read_bytes() + b"tamper")
            self.assertFalse(validate_compiled_clause(copied_point))
            copied_source.write_bytes(source.read_bytes())
            copied_point.write_text(point.replace(digest, "0" * 64, 1))
            self.assertFalse(validate_compiled_clause(copied_point))
            copied_point.write_text(point.replace("`C2-contract-fixture`", "`C2-other`", 1))
            self.assertFalse(validate_compiled_clause(copied_point))

    def test_literal_row6_accepts_ordered_log_and_rejects_reverse(self):
        valid = run_row(6, "row6/valid")
        invalid = run_row(6, "row6/invalid")
        cross = run_row(6, "row6/archive-newer")
        self.assertEqual(valid.returncode, 0)
        self.assertEqual(valid.stdout, "")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("row6: out of order", invalid.stdout)
        self.assertNotEqual(cross.returncode, 0)
        self.assertIn("row6: archive newer than log oldest", cross.stdout)
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "docs/plans/demo"
            workspace.mkdir(parents=True)
            result = subprocess.run(["sh", "-c", literal_row(6).replace("<slug>", "demo")],
                                    cwd=Path(temp), capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("row6: missing log.md", result.stdout)

    def test_literal_row11_checks_usage_and_guard_skips_legacy_workspace(self):
        valid = run_row(11, "row11/valid")
        legacy = run_row(11, "row11/legacy")
        self.assertEqual(valid.returncode, 0)
        self.assertEqual(valid.stdout, "")
        self.assertEqual(legacy.returncode, 0)
        self.assertEqual(legacy.stdout, "")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "docs/plans/demo"
            workspace.mkdir(parents=True)
            source = ROOT / "fixtures/contracts/row11/valid"
            shutil.copyfile(source / "board.md", workspace / "board.md")
            (workspace / "usage.md").write_text("| Run ID | Point |\n|---|---|\n| run | P-99 |\n")
            result = subprocess.run(["sh", "-c", literal_row(11).replace("<slug>", "demo")], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("row11: done point without usage row: P-01", result.stdout)
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "docs/plans/demo"
            workspace.mkdir(parents=True)
            (workspace / "usage.md").write_text("| Run ID | Point |\n|---|---|\n| run | P-01 |\n")
            result = subprocess.run(["sh", "-c", literal_row(11).replace("<slug>", "demo")],
                                    cwd=Path(temp), capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("row11: missing board.md", result.stdout)

    def test_literal_row16_checks_actual_workspace_lifecycle(self):
        valid = run_row(16, "row16/valid")
        invalid = run_row(16, "row16/invalid")
        malformed = run_row(16, "row16/malformed")
        self.assertEqual(valid.returncode, 0)
        self.assertEqual(valid.stdout, "")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("row16: line 3:", invalid.stdout)
        self.assertIn("terminal before start", invalid.stdout)
        self.assertIn("Point/Role changed", invalid.stdout)
        self.assertNotEqual(malformed.returncode, 0)
        for message in ["unknown Event", "missing Run ID", "missing Point", "missing Role",
                        "missing, invalid, or negative Attempts/Rework",
                        "malformed data row"]:
            self.assertIn(message, malformed.stdout)
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "docs/plans/demo"
            workspace.mkdir(parents=True)
            result = subprocess.run(["sh", "-c", literal_row(16).replace("<slug>", "demo")],
                                    cwd=Path(temp), capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("row16: missing usage.md", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
