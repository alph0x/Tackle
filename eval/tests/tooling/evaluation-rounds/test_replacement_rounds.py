"""Public consumer tests for replacing a stopped round with an extended child round.

A child round keeps its parent's exact limits unless its opening cites an
owner extension receipt; with one, a limit may grow but never fall. The tests
drive the actual round CLI through the harness of the existing round family,
without inheriting its test methods.
"""

import copy
import importlib.util
import json
from pathlib import Path
import unittest


_SPEC = importlib.util.spec_from_file_location(
    "round_family", Path(__file__).resolve().with_name("test_rounds.py"))
family = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(family)

Harness = type("Harness", (unittest.TestCase,), {
    name: value for name, value in vars(family.RoundConsumerTests).items()
    if not name.startswith("test_")})


class ReplacementRoundTests(Harness):
    def stopped_parent(self, root):
        """A two-unit parent whose first unit failed on infrastructure and which then stopped."""
        value = family.spec(root, cases=1, arms=("A", "B"), n_min=1)
        parent = self.round(root, value, name="parent")
        receipt, _, _ = self.start(root, parent, value["order"][0]["unit_id"])
        self.assertTrue(receipt["dispatch_allowed"])
        self.finish(root, parent, value["order"][0], status="infrastructure-failure",
                    correct=False)
        result, result_path = self.compute(root, parent, "infrastructure-failure",
                                           name="parent-result")
        return value, result, result_path

    def child(self, root, parent_value, result, result_path, *, arms, units_limit,
              extension=True):
        value = family.spec(root, cases=1, arms=arms, n_min=1)
        value["round_id"] = "child-round"
        value["budgets"] = {key: dict(unit=key, limit=units_limit * family.RESERVATION[key])
                            for key in family.DIMENSIONS}
        parent_ref = family.ref(root, result_path)
        value["opening"] = dict(
            reserved=copy.deepcopy(result["summary"]["reserved"]),
            known_consumed=copy.deepcopy(result["summary"]["known_consumed"]),
            unknown=copy.deepcopy(result["summary"]["unknown"]),
            corrections=result["summary"]["corrections"],
            parent_receipt=parent_ref, new_allocation_receipt=None)
        if extension:
            decision = family.put(root / "public/owner-extension.json",
                                  {"owner": "one replacement episode for the stopped unit"})
            value["opening"]["extension_receipt"] = family.ref(root, decision)
        value["lineage"] = dict(budget_pool_id=parent_value["lineage"]["budget_pool_id"],
                                parent_result=parent_ref)
        return value

    def test_extension_lets_exactly_the_authorized_units_start(self):
        with self.lab() as root:
            parent_value, result, result_path = self.stopped_parent(root)
            # The parent allowed 2 units and reserved 1; the owner extends it to 3.
            value = self.child(root, parent_value, result, result_path,
                               arms=("A", "B", "C"), units_limit=3)
            child = self.round(root, value, name="child")
            for row in value["order"][:2]:
                receipt, _, _ = self.start(root, child, row["unit_id"])
                self.assertTrue(receipt["dispatch_allowed"])
                self.finish(root, child, row)
            refused = self.start(root, child, value["order"][2]["unit_id"], expected=(2,))[0]
            self.assertIn(b"reservation exceeds budget", refused.stderr)

    def test_without_extension_child_keeps_exact_parent_limits(self):
        with self.lab() as root:
            parent_value, result, result_path = self.stopped_parent(root)
            grown = self.child(root, parent_value, result, result_path,
                               arms=("A", "B", "C"), units_limit=3, extension=False)
            path = family.put(root / "grown.spec.json", grown)
            child = self.cli(root, "seal", "--spec", path, "--round", root / "grown",
                             expected=(2,))
            self.assertIn(b"parent budget unit/limit mismatch", child.stderr)
            same = self.child(root, parent_value, result, result_path,
                              arms=("A", "B"), units_limit=2, extension=False)
            exact = self.round(root, same, name="exact")
            receipt, _, _ = self.start(root, exact, same["order"][0]["unit_id"])
            self.assertTrue(receipt["dispatch_allowed"])
            self.finish(root, exact, same["order"][0])
            refused = self.start(root, exact, same["order"][1]["unit_id"], expected=(2,))[0]
            self.assertIn(b"reservation exceeds budget", refused.stderr)

    def test_extension_faults_are_refused_at_seal(self):
        with self.lab() as root:
            parent_value, result, result_path = self.stopped_parent(root)
            base = self.child(root, parent_value, result, result_path,
                              arms=("A", "B", "C"), units_limit=3)
            lowered = copy.deepcopy(base)
            lowered["budgets"]["turns"]["limit"] = family.RESERVATION["turns"]
            orphan = family.spec(root, cases=1, arms=("A", "B"), n_min=1)
            orphan["opening"]["extension_receipt"] = copy.deepcopy(
                base["opening"]["extension_receipt"])
            tampered = copy.deepcopy(base)
            tampered["opening"]["extension_receipt"]["sha256"] = "0" * 64
            drifted = copy.deepcopy(base)
            drifted["opening"]["reserved"]["episodes"] = 0
            for name, value, message in (
                    ("lowered", lowered, b"an extension cannot lower a parent limit"),
                    ("orphan", orphan, b"an extension receipt requires a parent result"),
                    ("tampered", tampered, b"extension receipt"),
                    ("drifted", drifted, b"opening does not match parent summary")):
                path = family.put(root / (name + ".spec.json"), value)
                child = self.cli(root, "seal", "--spec", path, "--round", root / name,
                                 expected=(2,))
                self.assertIn(message, child.stderr, name)
                self.assertFalse((root / name).exists(), name)

    def test_extended_child_replays_byte_identically(self):
        with self.lab() as root:
            parent_value, result, result_path = self.stopped_parent(root)
            value = self.child(root, parent_value, result, result_path,
                               arms=("A", "B"), units_limit=3)
            child = self.round(root, value, name="child")
            # B wins its pair against A, so the child's decision is decidable and the round succeeds.
            self.complete(root, child, value, observations={
                row["unit_id"]: (dict(correct=False) if row["arm"] == "A" else {})
                for row in value["order"]})
            child_result, child_path = self.compute(root, child, "success", name="child-result")
            self.assertEqual(child_result["lineage"]["parent_result"],
                             family.ref(root, result_path))
            self.replay(root, child, child_path, "success")


if __name__ == "__main__":
    unittest.main()
