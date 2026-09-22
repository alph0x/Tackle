"""P-04 executable witnesses for resumable Run and integrated acceptance."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_protocol", ROOT / "fixtures/run-protocol/protocol.py")
protocol = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = protocol
spec.loader.exec_module(protocol)
RUN = (ROOT.parent.parent / "references/guides/run.md").read_text()


class RunProtocol(unittest.TestCase):
    def test_protocol_has_one_state_machine_and_integrated_close_bar(self):
        for phrase in [
            "single execution protocol", "explicit execution intent", "Ready → preflight",
            "target validation", "integration validation", "deliverable acceptance", "complete",
            "`board.md`\nis the canonical current state", "`log.md` is append-only history",
        ]:
            self.assertIn(phrase, RUN)
        self.assertEqual(RUN.count("## State transitions"), 1)
        self.assertIn("All tasks passing is insufficient", RUN)

    def test_cents_dollars_mismatch_blocks_global_acceptance_with_green_units(self):
        self.assertFalse(protocol.global_acceptance(
            producer_cents=500, consumer_expected="5.00\n", package_output="500.00\n",
            local_units_green=True))
        self.assertFalse(protocol.global_acceptance(
            producer_cents=500, consumer_expected="5.00\n", package_output=None,
            local_units_green=True))
        self.assertTrue(protocol.global_acceptance(
            producer_cents=500, consumer_expected="5.00\n", package_output="5.00\n",
            local_units_green=True))

    def test_correction_count_serializes_and_third_failure_blocks(self):
        state = protocol.RunState()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            self.assertFalse(protocol.correction(state, success=False, observation="wrong output"))
            state.save(path)
            resumed = protocol.RunState.load(path)
            self.assertEqual(resumed.point_cycles, 1)
            self.assertTrue(protocol.correction(resumed, success=True, observation="corrected"))
            self.assertEqual(resumed.point_cycles, 1)
            self.assertFalse(protocol.correction(resumed, success=False, observation="different output"))
            self.assertFalse(protocol.correction(resumed, success=False, observation="third output"))
            self.assertEqual(resumed.point_cycles, 3)
            self.assertEqual(resumed.status, "blocked")

    def test_identical_no_progress_stops_before_three_cycles(self):
        state = protocol.RunState()
        self.assertFalse(protocol.correction(state, success=False, observation="same"))
        self.assertFalse(protocol.correction(state, success=False, observation="same"))
        self.assertEqual(state.point_cycles, 2)
        self.assertEqual(state.status, "blocked")

    def test_unowned_integration_pool_is_initiative_wide_and_transfer_is_once(self):
        state = protocol.RunState()
        self.assertTrue(protocol.unowned_integration(state, fault_id="fault-a"))
        self.assertFalse(protocol.unowned_integration(state, fault_id="fault-b"))
        self.assertEqual(state.integration_cycles, 2)
        state = protocol.RunState()
        self.assertTrue(protocol.unowned_integration(state, fault_id="fault-a"))
        self.assertTrue(protocol.unowned_integration(state, fault_id="fault-a", owner="P-02"))
        self.assertEqual(state.integration_owner_cycles, {"P-02": 1})
        self.assertEqual(state.point_cycles, 0)
        self.assertFalse(protocol.unowned_integration(state, fault_id="fault-b"))
        self.assertFalse(protocol.unowned_integration(state, fault_id="fault-b", owner="P-03"))
        self.assertEqual(state.integration_owner_cycles, {"P-02": 1, "P-03": 1})
        self.assertFalse(protocol.unowned_integration(state, fault_id="fault-b", owner="P-03"))
        self.assertEqual(state.integration_owner_cycles, {"P-02": 1, "P-03": 1})

    def test_attributed_integration_charge_consumes_current_point_budget(self):
        state = protocol.RunState(current_point_id="P-01", point_cycles=2)
        state.owner_total_cycles["P-01"] = 2
        self.assertTrue(protocol.unowned_integration(state, fault_id="fault-a"))
        self.assertFalse(protocol.unowned_integration(state, fault_id="fault-a", owner="P-01"))
        self.assertEqual(state.owner_total_cycles["P-01"], 3)
        self.assertEqual(state.point_cycles, 3)
        self.assertEqual(state.status, "blocked")

    def test_attribution_then_two_later_failures_blocks_and_survives_resume(self):
        state = protocol.RunState(current_point_id="P-01")
        self.assertTrue(protocol.unowned_integration(state, fault_id="fault-a"))
        self.assertTrue(protocol.unowned_integration(state, fault_id="fault-a", owner="P-01"))
        self.assertEqual(state.owner_total_cycles["P-01"], 1)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            state.save(path)
            resumed = protocol.RunState.load(path)
            self.assertEqual(resumed.owner_total_cycles["P-01"], 1)
            self.assertFalse(protocol.correction(resumed, success=False, observation="first"))
            self.assertFalse(protocol.correction(resumed, success=False, observation="second"))
            self.assertEqual(resumed.owner_total_cycles["P-01"], 3)
            self.assertEqual(resumed.status, "blocked")
    def test_child_failure_timeout_and_signal_cannot_hide_behind_wrapper(self):
        failed = protocol.observe_child([sys.executable, "-c", "raise SystemExit(7)"])
        timed = protocol.observe_child([sys.executable, "-c", "import time; time.sleep(1)"], timeout=.01)
        signaled = protocol.observe_child([sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"])
        self.assertFalse(protocol.wrapper_passes(failed, artifact=True))
        self.assertFalse(protocol.wrapper_passes(timed, artifact=True))
        self.assertLess(signaled["exit"], 0)
        self.assertEqual(signaled["signal"], 15)
        self.assertFalse(protocol.wrapper_passes(signaled, artifact=True))
        self.assertTrue(protocol.wrapper_passes({"exit": 0, "timeout": False, "signal": None}, artifact=True))

    def test_contract_defect_emits_packet_without_retry_or_frontier_dispatch(self):
        packet = protocol.failure_packet(
            cause="validator", requirement="C5@rev1", expected="reject missing package",
            observed="validator accepted it", reproducer="case-missing-package",
            consumers=["global acceptance"], attempts=1,
            decision="smallest unresolved decision: repair validator contract")
        state = protocol.RunState()
        stopped, packet = protocol.stop_for_nonimplementation(state, packet)
        self.assertEqual(stopped.status, "blocked")
        self.assertEqual(stopped.point_cycles, 0)
        self.assertEqual(packet["cause"], "validator")
        self.assertEqual(packet["attempts"], 1)
        self.assertIn("expected", packet)
        self.assertIn("observed", packet)
        self.assertIn("reproducer", packet)
        self.assertIn("consumers", packet)
        self.assertIn("decision", packet)
        self.assertNotIn("retry", packet)
        self.assertNotIn("dispatch", packet)

    def test_same_agent_observation_is_real_but_not_independent_review(self):
        observed = protocol.independent_evidence(actor="maker", maker="maker", isolated=True)
        independent = protocol.independent_evidence(actor="reviewer", maker="maker", isolated=True)
        unavailable = protocol.independent_evidence(actor="reviewer", maker="maker", isolated=False)
        self.assertEqual(observed["provenance"], "command-observed")
        self.assertFalse(observed["independent"])
        self.assertTrue(independent["independent"])
        self.assertFalse(unavailable["independent"])
        self.assertEqual(unavailable["provenance"], "unavailable")

    def test_semantic_consumers_beyond_file_touches_are_invalidated_selectively(self):
        consumers = {
            "producer": ["source"], "package": ["source", "config"],
            "docs": ["docs"], "integration": ["package"],
        }
        invalid = protocol.invalidate_consumers(consumers, ["source"])
        self.assertEqual(invalid, {"producer": True, "package": True,
                                   "docs": False, "integration": True})

    def test_required_independence_missing_is_blocked_without_fabricated_grade(self):
        evidence = protocol.independent_evidence(actor="reviewer", maker="maker", isolated=False)
        self.assertFalse(evidence["independent"])
        self.assertIn("provenance", evidence)
        self.assertEqual(evidence["provenance"], "unavailable")
        self.assertNotEqual(evidence.get("grade"), "E1")

    def test_missing_environment_blocks_preflight_with_named_capabilities(self):
        ready, missing = protocol.preflight({"python": True, "isolation": False, "package": True})
        self.assertFalse(ready)
        self.assertEqual(missing, ["isolation"])

    def test_interrupted_side_effect_preserves_history_before_continuation(self):
        history, action = protocol.resume_side_effect(["start", "side-effect-started"], "unknown")
        self.assertEqual(action, "inspect")
        self.assertEqual(history[-1], "observe-incomplete")
        preserved, action = protocol.resume_side_effect(history, "occurred")
        self.assertEqual(action, "preserve")
        self.assertEqual(preserved, history)

    def test_docs_bind_templates_to_run_without_competing_loops(self):
        team = (ROOT.parent.parent / "references/team.tmpl.md").read_text()
        agents = (ROOT.parent.parent / "references/AGENTS.tmpl.md").read_text()
        coordinator = (ROOT.parent.parent / "references/coordinator.tmpl.md").read_text()
        for text in [team, agents, coordinator]:
            self.assertIn("references/guides/run.md", text)
            self.assertNotIn("Pre-wave verification gate", text)
            self.assertNotIn("Rework bound", text)
        self.assertIn("non-goals are explicit exclusions", agents)
        self.assertIn("Initiative unowned-integration cycles", coordinator)


if __name__ == "__main__":
    unittest.main()
