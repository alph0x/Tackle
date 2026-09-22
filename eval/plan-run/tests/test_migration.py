import hashlib
import re
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def heading_fragment(line):
    return re.sub(r"[^a-z0-9 -]", "", line.lower()).strip().replace(" ", "-")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_world(root):
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for name in ("selected", "closed", "unrelated", "neighbor")
        for path in (root / name).rglob("*")
        if path.is_file()
    }


def assert_world_unchanged(root, expected):
    actual = snapshot_world(root)
    if actual != expected:
        raise ValueError("closed, unrelated, neighbor or selected workspace changed")


def write_legacy_world(root):
    workspace = root / "selected/docs/plans/legacy"
    (workspace / "points").mkdir(parents=True)
    (root / "neighbor").mkdir()
    (root / "unrelated").mkdir()
    (workspace / "AGENTS.md").write_text("# Legacy workspace\n\nMethodology: Tackle 7.3.0\n")
    (workspace / "board.md").write_text(
        "# Board\n\n| Point | Status | Confidence |\n|---|---|---|\n"
        "| P-01 | 🔴 | n/a |\n| P-02 | 🟢 | E1 |\n"
        "| P-03 | ⏸ | E0 |\n| P-04 | ⚪ | E3 |\n| P-05 | 🟡 | E0 |\n"
    )
    (workspace / "log.md").write_text(
        "# Log — legacy fixture\n\n## 2026-09-01 · session 1 · legacy state\n\n"
        "### State snapshot\n- Done: P-02\n- In flight: P-05, interrupted\n"
        "- Blocked on: P-03 external input\n- Resume from: P-05 pinned legacy procedure\n"
    )
    (workspace / "usage.md").write_text(
        "| Run ID | State | Point | Tokens |\n|---|---|---|---|\n"
        "| legacy-1 | finish | P-02 | n/a |\n| legacy-2 | observe-incomplete | P-05 | n/a |\n"
    )
    (workspace / "contract-v7.3.md").write_text(
        "# Legacy contract\n\nrevision: 7.3.0\noutputs: historical fields\n"
    )
    (workspace / "evidence").mkdir()
    (workspace / "evidence/P-02-finish.md").write_text(
        "# P-02 evidence\n\nlegacy command: fixture-finish\nexit: 0\n"
    )
    (workspace / "points/P-01.md").write_text("# P-01 — Unstarted legacy point\n\nStatus: not started\n")
    (workspace / "points/P-03.md").write_text(
        "# P-03 — Blocked legacy point\n\nWaiting for external input.\n"
    )
    (workspace / "points/P-05.md").write_text(
        "# P-05 — Interrupted legacy point\n\nPinned procedure: legacy execution\n"
    )
    (root / "neighbor/sentinel.txt").write_text("neighbor-preserved\n")
    (root / "unrelated/README.md").write_text("unrelated-workspace-preserved\n")
    (root / "closed/docs/plans/legacy").mkdir(parents=True)
    (root / "closed/docs/plans/legacy/board.md").write_text(
        "# Closed workspace\n\n| Point | Status |\n|---|---|\n| P-09 | 🟢 |\n"
    )
    return workspace


def status_query(workspace):
    return {
        "board": (workspace / "board.md").read_text(),
        "log": (workspace / "log.md").read_text(),
    }


def prepare_migration(selected, trial):
    shutil.copytree(selected, trial)
    workspace = trial / "docs/plans/legacy"
    board = (workspace / "board.md").read_text()
    if "| P-01 | 🔴" not in board:
        raise ValueError("selected workspace has no unstarted work")
    if "| P-05 | 🟡" not in board:
        raise ValueError("interrupted Point is not pinned")
    contract = workspace / "contract-v7.3.md"
    if not contract.is_file():
        raise ValueError("legacy contract is missing")
    contract_bytes = contract.read_bytes()
    contract_hash = hashlib.sha256(contract_bytes).hexdigest()
    (workspace / "compiled").mkdir()
    (workspace / "compiled/P-01.md").write_text(
        "# P-01 — Current compiled Point\n\n"
        "Revision: candidate-8.0\n"
        "Purpose: migrate the selected active slice while retaining legacy records.\n"
        "Requirements: preserve contract, evidence, statuses, log bytes and usage bytes;\n"
        "compile only unstarted P-01; keep interrupted P-05 pinned to its old procedure.\n"
        "Interface: input selected workspace copy; output points/P-01-v8.md at boundary.\n"
        "Cases: P-01 unstarted; P-02 completed; P-03 blocked; P-04 skipped; P-05 interrupted.\n"
        "Constraints: Touch selected copy only; closed, unrelated and neighbor paths are outside scope.\n"
        "Non-goals: no closed-work re-execution, evidence re-grade, history rewrite or release.\n"
        "Strategy: copy first, verify readiness, then append selective adoption at Point boundary.\n"
        "Target: migration checks pass with exit 0; Surround: affected suite remains green.\n"
        "Recovery: restore separate rollback copy from checkpoint and compare all bytes.\n"
        "Contract revision: 7.3.0\n"
        f"Contract bytes sha256: {contract_hash}\n"
        "Contract snapshot:\n" + contract_bytes.decode("utf-8") +
        "Readiness: pending\n"
    )
    return workspace


def adopt_at_boundary(trial, point_id):
    workspace = trial / "docs/plans/legacy"
    board = (workspace / "board.md").read_text()
    if point_id != "P-01" or "| P-01 | 🔴" not in board:
        raise ValueError("adoption requires the selected Point boundary")
    compiled = workspace / "compiled/P-01.md"
    compiled_text = compiled.read_text()
    if "Readiness: checked" not in compiled_text:
        raise ValueError("readiness is pending")
    expected_hash = next(
        (line.split(": ", 1)[1] for line in compiled_text.splitlines()
         if line.startswith("Contract bytes sha256: ")),
        None,
    )
    if expected_hash != sha256(workspace / "contract-v7.3.md"):
        raise ValueError("contract changed after compilation")
    (workspace / "points/P-01-v8.md").write_text(
        compiled_text + "Adopted fields: current outputs only\n"
    )
    (workspace / "adoption.md").write_text(
        "candidate: candidate-8.0\npoint: P-01\nappend-only: true\n"
    )


def validate_history(trial, expected):
    workspace = trial / "docs/plans/legacy"
    actual = {name: sha256(workspace / name) for name in expected}
    if actual != expected:
        raise ValueError("legacy history changed")


class MigrationContract(unittest.TestCase):
    def test_public_surface_has_two_actions_and_readonly_status(self):
        skill = (ROOT / "SKILL.md").read_text()
        readme = (ROOT / "README.md").read_text()
        for text in (skill, readme):
            self.assertIn("PLAN", text)
            self.assertIn("RUN", text)
            self.assertIn("STATUS", text)
            self.assertIn("Tackle 8.1.0", text)
            self.assertNotIn("candidate protocol 8.0 is unpublished", text)
        self.assertIn("`run --one`", skill)
        invocation = (ROOT / "references/guides/invocation.md").read_text()
        self.assertIn("/tackle-run --one", invocation)
        self.assertIn("aliases", skill)
        self.assertIn("retire in 9.0", skill)
        self.assertNotIn("public surface at eight commands", skill)

    def test_status_has_no_log_write_exception(self):
        status = (ROOT / "references/guides/status.md").read_text()
        self.assertIn("never executes a task or edits source, task board,\nhistory", status)
        self.assertIn("Only an explicit handoff request may write", status)
        self.assertNotIn("only write allowed is an optional `log.md` entry", status)
        self.assertIn("STATUS never archives history or appends a status event", status)

    def test_aliases_preserve_query_and_execution_intent(self):
        skill = (ROOT / "SKILL.md").read_text()
        self.assertIn("implement` → RUN", skill)
        self.assertIn("ground`/`trace`/`drill` → PLAN validation", skill)
        self.assertIn("pulse`/`list`/`next`/`resume` → STATUS", skill)
        self.assertIn("handoff` → STATUS `--handoff`", skill)
        self.assertIn("explicit resume request that also states execution intent", skill)

    def test_copy_first_migration_preserves_history_and_neighbor(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = write_legacy_world(root)
            selected = root / "selected"
            log, usage = workspace / "log.md", workspace / "usage.md"
            world_before = snapshot_world(root)
            before = {path.relative_to(selected).as_posix(): sha256(path)
                      for path in selected.rglob("*") if path.is_file()}
            checkpoint = root / "checkpoint"
            shutil.copytree(selected, checkpoint)
            original_point = (workspace / "points/P-05.md").read_bytes()
            trial = root / "trial"
            trial_workspace = prepare_migration(selected, trial)
            assert_world_unchanged(root, world_before)
            (trial_workspace / "migration-record.md").write_text(
                "candidate: 8.0\nreadiness: pending\nselected: active\n"
            )
            self.assertIn("revision: 7.3.0", (trial_workspace / "contract-v7.3.md").read_text())
            compiled_text = (trial_workspace / "compiled/P-01.md").read_text()
            self.assertIn("Contract snapshot:", compiled_text)
            self.assertIn("Requirements: preserve contract, evidence", compiled_text)
            self.assertIn("Cases: P-01 unstarted; P-02 completed; P-03 blocked; P-04 skipped; P-05 interrupted.", compiled_text)
            self.assertIn("Contract bytes sha256:", compiled_text)
            self.assertEqual(
                sha256(trial_workspace / "evidence/P-02-finish.md"),
                sha256(workspace / "evidence/P-02-finish.md"),
            )
            self.assertEqual(before["docs/plans/legacy/log.md"], sha256(log))
            self.assertEqual(before["docs/plans/legacy/usage.md"], sha256(usage))
            self.assertEqual((workspace / "board.md").read_text().count("| P-02 | 🟢"), 1)
            self.assertIn("| P-03 | ⏸", (workspace / "board.md").read_text())
            self.assertIn("| P-04 | ⚪", (workspace / "board.md").read_text())
            self.assertIn("| P-05 | 🟡", (workspace / "board.md").read_text())
            self.assertEqual(original_point, (workspace / "points/P-05.md").read_bytes())
            assert_world_unchanged(root, world_before)
            rollback = root / "rollback"
            shutil.copytree(checkpoint, rollback)
            rollback_selected = rollback / "docs/plans/legacy"
            self.assertEqual(
                before,
                {path.relative_to(rollback).as_posix(): sha256(path)
                 for path in rollback.rglob("*") if path.is_file()},
            )
            self.assertFalse((rollback_selected / "migration-record.md").exists())
            self.assertFalse((rollback_selected / "compiled").exists())
            self.assertTrue((rollback_selected / "contract-v7.3.md").exists())
            assert_world_unchanged(root, world_before)

    def test_operational_migration_guards_query_adoption_and_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            selected = root / "selected"
            write_legacy_world(root)
            workspace = selected / "docs/plans/legacy"
            world_before = snapshot_world(root)
            before = {name: sha256(workspace / name) for name in ("log.md", "usage.md")}
            legacy_contract = (workspace / "contract-v7.3.md").read_bytes()
            legacy_evidence = (workspace / "evidence/P-02-finish.md").read_bytes()
            query_before = status_query(workspace)
            self.assertEqual(query_before, status_query(workspace))
            trial = root / "trial"
            trial_workspace = prepare_migration(selected, trial)
            assert_world_unchanged(root, world_before)
            compiled = trial_workspace / "compiled/P-01.md"
            compiled_text = compiled.read_text()
            self.assertIn("Revision: candidate-8.0", compiled_text)
            self.assertIn("Interface: input selected workspace copy; output points/P-01-v8.md at boundary.", compiled_text)
            self.assertIn("Contract snapshot:", compiled_text)
            self.assertEqual((trial_workspace / "contract-v7.3.md").read_bytes(), legacy_contract)
            self.assertEqual((trial_workspace / "evidence/P-02-finish.md").read_bytes(), legacy_evidence)
            self.assertIn("Pinned procedure: legacy execution", (trial_workspace / "points/P-05.md").read_text())
            with self.assertRaises(ValueError):
                adopt_at_boundary(trial, "P-05")
            with self.assertRaises(ValueError):
                adopt_at_boundary(trial, "P-01")
            compiled.write_text(compiled.read_text().replace("Readiness: pending", "Readiness: checked"))
            (trial_workspace / "contract-v7.3.md").write_bytes(legacy_contract + b"changed after compile\n")
            with self.assertRaises(ValueError):
                adopt_at_boundary(trial, "P-01")
            self.assertFalse((trial_workspace / "adoption.md").exists())
            self.assertFalse((trial_workspace / "points/P-01-v8.md").exists())
            (trial_workspace / "contract-v7.3.md").write_bytes(legacy_contract)
            adopt_at_boundary(trial, "P-01")
            self.assertTrue((trial_workspace / "adoption.md").exists())
            self.assertIn("Adopted fields: current outputs only", (trial_workspace / "points/P-01-v8.md").read_text())
            assert_world_unchanged(root, world_before)
            validate_history(trial, before)
            (trial_workspace / "log.md").write_text("tampered\n")
            with self.assertRaises(ValueError):
                validate_history(trial, before)
            assert_world_unchanged(root, world_before)

            closed_board = root / "closed/docs/plans/legacy/board.md"
            closed_before = closed_board.read_bytes()
            closed_board.write_bytes(b"monkeypatched closed workspace\n")
            with self.assertRaises(ValueError):
                assert_world_unchanged(root, world_before)
            closed_board.write_bytes(closed_before)
            assert_world_unchanged(root, world_before)

    def test_heading_fragment_excludes_heading_separator(self):
        headings = {heading_fragment(line) for line in [
            "## Execute canonical lint faithfully", "# Prepare once, then capture"]}
        self.assertIn("execute-canonical-lint-faithfully", headings)
        self.assertIn("prepare-once-then-capture", headings)
        self.assertNotIn("-execute-canonical-lint-faithfully", headings)
        self.assertNotIn("missing-heading", headings)

    def test_install_is_markdown_only_and_links_resolve(self):
        with tempfile.TemporaryDirectory() as temp:
            install = Path(temp) / "skill"
            install.mkdir()
            shutil.copy2(ROOT / "SKILL.md", install / "SKILL.md")
            shutil.copytree(ROOT / "references", install / "references")
            files = list(install.rglob("*"))
            self.assertTrue(files)
            self.assertTrue(all(p.is_dir() or p.suffix == ".md" for p in files))
            text = "\n".join(p.read_text() for p in install.rglob("*.md"))
            self.assertNotIn("docs/plans/tackle-plan-run", text)
            for source in install.rglob("*.md"):
                for link in re.findall(r"\]\(([^)]+)\)", source.read_text()):
                    target, _, fragment = link.partition("#")
                    if not target or target.startswith(("http:", "https:", "mailto:")):
                        continue
                    if "<" in target or "{{" in target or target.startswith("docs/plans/"):
                        continue
                    destination = (source.parent / target).resolve()
                    if destination.is_file() and fragment:
                        headings = {heading_fragment(line)
                                    for line in destination.read_text().splitlines() if line.startswith("#")}
                        headings.update(re.findall(r'<a id="([^"]+)"', destination.read_text()))
                        self.assertIn(fragment.lower(), headings, link)
                    elif target.startswith(("references/", "guides/", "../")):
                        self.assertTrue(destination.is_file(), link)


if __name__ == "__main__":
    unittest.main()
