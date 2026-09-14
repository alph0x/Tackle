"""Small executable witness for the P-04 state and evidence rules.

This fixture models protocol decisions only; it never runs an agent or authorizes repository edits.
"""
from dataclasses import asdict, dataclass, field
import json
import subprocess
from pathlib import Path


@dataclass
class RunState:
    current_point_id: str = "P-01"
    point_cycles: int = 0
    owner_total_cycles: dict = field(default_factory=dict)
    no_progress: int = 0
    integration_cycles: int = 0
    integration_transferred: dict = field(default_factory=dict)
    integration_by_fault: dict = field(default_factory=dict)
    integration_owner_cycles: dict = field(default_factory=dict)
    status: str = "implementing"
    history: list = field(default_factory=list)

    def save(self, path):
        Path(path).write_text(json.dumps(asdict(self), sort_keys=True) + "\n")

    @classmethod
    def load(cls, path):
        return cls(**json.loads(Path(path).read_text()))


def correction(state, *, success, observation):
    """Apply one observed correction result, preserving counts across serialization."""
    if state.status == "blocked":
        return False
    state.history.append(observation)
    if success:
        state.status = "validating"
        state.no_progress = 0
        return True
    state.point_cycles += 1
    state.owner_total_cycles[state.current_point_id] = state.point_cycles
    repeated = len(state.history) > 1 and observation == state.history[-2]
    state.no_progress = state.no_progress + 1 if repeated else 1
    if state.point_cycles >= 3 or state.no_progress >= 2:
        state.status = "blocked"
    return False


def unowned_integration(state, *, fault_id="fault-1", owner=None):
    """Consume one initiative-wide slot, transferring it once after attribution."""
    if owner and fault_id not in state.integration_transferred:
        spent = state.integration_by_fault.get(fault_id, 0)
        state.integration_owner_cycles[owner] = state.integration_owner_cycles.get(owner, 0) + spent
        state.owner_total_cycles[owner] = state.owner_total_cycles.get(owner, 0) + spent
        state.integration_transferred[fault_id] = owner
        if owner == state.current_point_id:
            state.point_cycles = state.owner_total_cycles[owner]
            if state.point_cycles >= 3:
                state.status = "blocked"
    if owner:
        return state.status != "blocked" and state.owner_total_cycles.get(owner, 0) < 3
    state.integration_cycles += 1
    state.integration_by_fault[fault_id] = state.integration_by_fault.get(fault_id, 0) + 1
    if state.integration_cycles >= 2:
        state.status = "blocked"
    return state.status != "blocked"


def global_acceptance(*, producer_cents, consumer_expected, package_output, local_units_green=True):
    produced = f"{producer_cents / 100:.2f}\n"
    return (local_units_green and package_output is not None
            and produced == consumer_expected and package_output == consumer_expected)


def observe_child(command, timeout=2):
    try:
        child = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return {"exit": child.returncode, "timeout": False,
                "signal": -child.returncode if child.returncode < 0 else None,
                "stdout": child.stdout, "stderr": child.stderr}
    except subprocess.TimeoutExpired as error:
        return {"exit": None, "timeout": True, "signal": None,
                "stdout": error.stdout or "", "stderr": error.stderr or ""}


def wrapper_passes(child, artifact):
    return child["exit"] == 0 and child["timeout"] is False and child["signal"] is None and artifact


def failure_packet(*, cause, requirement, expected, observed, reproducer, consumers, attempts, decision):
    return {"cause": cause, "requirement": requirement, "expected": expected,
            "observed": observed, "reproducer": reproducer, "consumers": consumers,
            "attempts": attempts, "decision": decision}


def stop_for_nonimplementation(state, packet):
    """Nonimplementation defects stop affected work; they do not spend a fix retry."""
    state.status = "blocked"
    return state, packet


def independent_evidence(*, actor, maker, isolated):
    independent = actor != maker and isolated
    return {"actor": actor, "independent": independent,
            "provenance": ("command-observed" if actor == maker
                           else "independent-review" if isolated else "unavailable")}


def invalidate_consumers(consumers, changed_inputs):
    changed = set(changed_inputs)
    invalid = {}
    while True:
        additions = {name for name, inputs in consumers.items()
                     if name not in changed and set(inputs) & changed}
        if not additions:
            break
        changed.update(additions)
        invalid.update({name: True for name in additions})
    return {name: (name in changed) for name in consumers}


def preflight(capabilities):
    missing = sorted(name for name, available in capabilities.items() if not available)
    return not missing, missing


def resume_side_effect(state, occurrence):
    """Inspect before repeat; unknown occurrence leaves history and requests observation."""
    state = list(state)
    if occurrence == "occurred":
        return state, "preserve"
    if occurrence == "unknown":
        return state + ["observe-incomplete"], "inspect"
    return state + ["performed"], "execute"
