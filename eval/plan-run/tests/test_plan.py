"""Behavioral witnesses for PLAN readiness and handoff rules.

The witness is disposable development evidence. These tests do not claim that an agent obeyed
the Markdown protocol; they ensure the structured procedure has the required failure behavior.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "plan_procedure", ROOT / "fixtures/plan-protocol/procedure.py"
)
procedure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(procedure)


def requirement(observable="outputs:csv+json"):
    return {
        "id": "R-output",
        "observable": observable,
        "evidence_slot": "evidence/output",
    }


def point(observable="outputs:csv+json"):
    return {
        "id": "P-01",
        "cases": [{
            "criterion": "R-output",
            "observable": observable,
            "check": "check-output",
        }],
    }


def equivalent_requirement():
    return requirement({"outputs": ["csv", "json"], "order": "unspecified"})


def obligation():
    return {
        "id": "global-package",
        "owner": "coordinator",
        "check": "check-package",
        "evidence_slot": "evidence/package",
    }


class PlanProtocol(unittest.TestCase):
    def test_plan_template_keeps_stable_section_consumers(self):
        template = (ROOT.parent.parent / "references/plan.tmpl.md").read_text()
        headings = [
            "## 5. Point decomposition",
            "## 6. Readiness and acceptance",
            "### 6.1 Universal per-point acceptance",
            "### 6.2 Initiative-level acceptance",
        ]
        positions = [template.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(template.index("### Behavior and outputs"), positions[0])
        self.assertLess(template.index("### Acceptance and test strategy"), positions[0])

    def test_plan_preparation_stops_before_source_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            sentinel = Path(temp) / "source-sentinel"
            sentinel.write_text("protected")
            result = procedure.prepare(
                [requirement()], [point()], [obligation()],
                {"contract": "c1", "code": "s1", "config": "g1", "deps": "d1", "input": "i1"},
                {"positive": True, "negative": True},
            )
            self.assertFalse(result["execution_started"])
            self.assertFalse(result["product_pass"])
            self.assertEqual(sentinel.read_text(), "protected")
            self.assertEqual(result["intent"], procedure.PLAN_INTENT)

    def test_ids_do_not_hide_semantic_missing_output(self):
        result = procedure.prepare(
            [requirement()], [point("outputs:csv")], [obligation()],
            {"contract": "c1", "code": "s1"}, {"positive": True, "negative": True},
        )
        self.assertFalse(result["ready"])
        self.assertEqual(result["matrix"]["rows"][0]["status"], "gap")
        self.assertEqual(result["matrix"]["rows"][0]["points"], [])

    def test_global_obligation_and_scope_drift_block_ready(self):
        orphan = {"id": "P-02", "cases": []}
        result = procedure.prepare(
            [requirement()], [point(), orphan], [],
            {"contract": "c1"}, {"positive": True, "negative": True},
        )
        self.assertFalse(result["ready"])
        self.assertEqual(result["matrix"]["scope_drift"], ["P-02"])
        self.assertEqual(result["matrix"]["global"], [])

    def test_unowned_required_global_obligation_blocks_complete_points(self):
        missing_owner = {"id": "global-package", "owner": "", "check": "", "evidence_slot": ""}
        result = procedure.prepare(
            [requirement()], [point()], [missing_owner], {"contract": "c1"},
            {"positive": True, "negative": True},
        )
        self.assertFalse(result["ready"])
        self.assertEqual(result["matrix"]["global"][0]["status"], "gap")

    def test_semantic_equivalent_output_order_remains_valid(self):
        req = equivalent_requirement()
        reversed_case = point({"outputs": ["json", "csv"], "order": "unspecified"})
        self.assertTrue(procedure.coverage([req], [reversed_case], [obligation()])["rows"][0]["status"] == "covered")

    def test_wrong_cold_probe_fails_even_with_no_doubts(self):
        probe = procedure.cold_probe({"output": "ready"}, {"output": "blocked"}, [])
        self.assertFalse(probe["passed"])
        result = procedure.prepare(
            [requirement()], [point()], [obligation()], {"contract": "c1"},
            {"positive": True, "negative": True}, probe=probe,
        )
        self.assertFalse(result["ready"])

    def test_revalidation_is_selective_and_unchanged_sessions_reuse(self):
        consumers = {
            "planner": {"contract", "config"},
            "writer": {"contract"},
            "docs": {"documentation"},
        }
        before = {"contract": "c1", "config": "g1", "documentation": "d1"}
        unchanged = procedure.revalidate(before, dict(before), consumers)
        self.assertEqual(unchanged["invalidated"], [])
        self.assertFalse(unchanged["complete_reverify_required"])
        drift = procedure.revalidate(before, {**before, "config": "g2"}, consumers)
        self.assertEqual(drift["invalidated"], ["planner"])
        self.assertEqual(drift["reused"], ["docs", "writer"])
        docs_drift = procedure.revalidate(before, {**before, "documentation": "d2"}, consumers)
        self.assertEqual(docs_drift["invalidated"], ["docs"])
        removed = procedure.revalidate(before, {"contract": "c1", "documentation": "d1"}, consumers)
        self.assertEqual(removed["invalidated"], ["planner"])

    def test_ready_requires_both_fixture_directions_and_fingerprint(self):
        inputs = {"contract": "c1", "code": "s1", "config": "g1", "deps": "d1", "input": "i1"}
        result = procedure.prepare(
            [requirement()], [point()], [obligation()], inputs,
            {"positive": True, "negative": True},
        )
        self.assertTrue(result["ready"])
        self.assertEqual(len(result["fingerprint"]), 64)
        failed_fixture = procedure.prepare(
            [requirement()], [point()], [obligation()], inputs,
            {"positive": True, "negative": False},
        )
        self.assertFalse(failed_fixture["ready"])

    def test_missing_required_fingerprint_blocks_ready(self):
        result = procedure.prepare(
            [requirement()], [point()], [obligation()], {"contract": "c1"},
            {"positive": True, "negative": True},
        )
        self.assertFalse(result["ready"])

    def test_empty_plan_inputs_do_not_vacuously_pass(self):
        result = procedure.prepare([], [], [], {}, {"positive": True, "negative": True})
        self.assertFalse(result["ready"])
