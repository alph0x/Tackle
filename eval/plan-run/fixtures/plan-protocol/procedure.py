"""Disposable witness for PLAN readiness semantics.

This is development evidence only. It models the structured inputs and decisions that the
Markdown protocol requires; it is not an implementation runner and never executes source.
"""
import hashlib
import json


PLAN_INTENT = "INTENT: PLAN prepares Points and stops before source execution."


def _digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _observable_equal(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        if left.get("order") == right.get("order") == "unspecified":
            if set(left.get("outputs", [])) != set(right.get("outputs", [])):
                return False
            return all(
                left.get(key) == right.get(key)
                for key in set(left) | set(right)
                if key not in {"outputs", "order"}
            )
    return left == right


def coverage(requirements, points, global_obligations):
    point_ids = {point["id"] for point in points}
    rows = []
    for requirement in requirements:
        matches = []
        for point in points:
            for case in point.get("cases", []):
                if case.get("criterion") != requirement["id"]:
                    continue
                if _observable_equal(case.get("observable"), requirement["observable"]) and case.get("check"):
                    matches.append((point["id"], case["check"]))
        rows.append({
            "criterion": requirement["id"],
            "observable": requirement["observable"],
            "points": sorted({point for point, _ in matches}),
            "checks": sorted({check for _, check in matches}),
            "evidence_slot": requirement.get("evidence_slot"),
            "status": "covered" if matches and requirement.get("evidence_slot") else "gap",
        })

    covered_points = {point for row in rows for point in row["points"]}
    scope_drift = sorted(point_ids - covered_points)
    global_rows = [
        {
            "obligation": obligation["id"],
            "owner": obligation.get("owner"),
            "check": obligation.get("check"),
            "evidence_slot": obligation.get("evidence_slot"),
            "status": "covered" if all(obligation.get(key) for key in ("owner", "check", "evidence_slot")) else "gap",
        }
        for obligation in global_obligations
    ]
    return {"rows": rows, "scope_drift": scope_drift, "global": global_rows}


def cold_probe(expected, observed, doubts):
    """A confident but wrong output is still a failed probe."""
    return {
        "doubts": list(doubts),
        "expected": expected,
        "observed": observed,
        "passed": expected == observed and not doubts,
    }


def prepare(requirements, points, global_obligations, inputs, fixtures, *, probe=None):
    matrix = coverage(requirements, points, global_obligations)
    fixture_pass = all(fixtures.get(name) is True for name in ("positive", "negative"))
    probe_pass = probe is None or probe["passed"]
    required_inputs = {"contract", "code", "config", "deps", "input"}
    inputs_complete = required_inputs.issubset(inputs) and bool(requirements) and bool(points)
    ready = (
        inputs_complete
        and
        not matrix["scope_drift"]
        and all(row["status"] == "covered" for row in matrix["rows"])
        and all(row["status"] == "covered" for row in matrix["global"])
        and fixture_pass
        and probe_pass
    )
    return {
        "intent": PLAN_INTENT,
        "execution_started": False,
        "product_pass": False,
        "matrix": matrix,
        "fingerprint": _digest(inputs),
        "ready": ready,
        "probe": probe,
    }


def revalidate(previous_inputs, current_inputs, consumers):
    changed = {
        name for name in set(previous_inputs) | set(current_inputs)
        if previous_inputs.get(name) != current_inputs.get(name)
    }
    invalidated = sorted(
        consumer for consumer, dependencies in consumers.items()
        if changed.intersection(dependencies)
    )
    return {
        "changed": sorted(changed),
        "invalidated": invalidated,
        "reused": sorted(set(consumers) - set(invalidated)),
        "complete_reverify_required": False,
    }
