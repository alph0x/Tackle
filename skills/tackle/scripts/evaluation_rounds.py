#!/usr/bin/env python3
"""Finite, local evaluation-round sealing, reservation, computation and replay."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys

SCHEMA = "tackle-round/1"
RECEIPT_SCHEMA = "tackle-round-receipt/1"
RESULT_SCHEMA = "tackle-round-result/1"
DIMENSIONS = ("episodes", "turns", "judgment_requests", "wall_ms")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")

class RoundError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def canonical(value):
    try:
        return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RoundError("noncanonical JSON value: %s" % exc) from exc


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key] = value
    return out


def _constant(value):
    raise ValueError("nonfinite JSON number")


def read_json(path):
    try:
        return json.loads(Path(path).read_bytes().decode("utf-8"),
                          object_pairs_hook=_pairs, parse_constant=_constant)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise RoundError("invalid JSON %s: %s" % (path, exc)) from exc


def require(condition, message, code=2):
    if not condition:
        raise RoundError(message, code)


def object_shape(value, keys, label):
    require(type(value) is dict and set(value) == set(keys),
            "%s must have exactly %s" % (label, ", ".join(keys)))


def nonempty(value, label):
    require(type(value) is str and bool(value.strip()), "%s must be a nonempty string" % label)
    return value


def ident(value, label):
    nonempty(value, label)
    require(ID_RE.fullmatch(value) is not None, "%s has invalid identifier syntax" % label)
    return value


def integer(value, label, minimum=0):
    require(type(value) is int and value >= minimum, "%s must be an integer >= %d" % (label, minimum))
    return value


def contained_path(root, candidate, label, directory):
    base = Path(root).resolve()
    path = Path(candidate)
    if not path.is_absolute():
        path = base / path
    try:
        parts = path.relative_to(base).parts
    except ValueError as exc:
        raise RoundError("%s path escapes cwd" % label) from exc
    require(".." not in parts, "%s path contains a parent component" % label)
    current = base
    for index, part in enumerate(parts):
        current = current / part
        require(not current.is_symlink(), "%s path contains a symlink" % label)
        is_directory = directory or index < len(parts) - 1
        require(current.is_dir() if is_directory else current.is_file(),
                "%s path is missing or has the wrong type" % label)
    require(current.is_dir() if directory else current.is_file(),
            "%s path has the wrong type" % label)
    return current


def contained_file(root, rel, label, expected_hash=None):
    require(type(rel) is str and rel and not Path(rel).is_absolute(), "%s path must be relative" % label)
    path = contained_path(root, rel, label, False)
    data = path.read_bytes()
    if expected_hash is not None:
        require(type(expected_hash) is str and HASH_RE.fullmatch(expected_hash) is not None,
                "%s sha256 is invalid" % label)
        require(digest(data) == expected_hash, "%s bytes do not match declared sha256" % label)
    return path


def contained_dir(root, rel, label):
    require(type(rel) is str and Path(rel).is_absolute(), "%s must be an absolute path" % label)
    return contained_path(root, rel, label, True)


def ref_check(root, value, label):
    object_shape(value, ("path", "sha256"), label)
    return contained_file(root, value["path"], label, value["sha256"])


def canonical_ref(root, value, label):
    path = ref_check(root, value, label)
    data = path.read_bytes()
    parsed = _loads(data, label)
    require(canonical(parsed) == data, "%s must contain canonical JSON bytes" % label)
    return parsed


def _loads(data, label):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeError, ValueError) as exc:
        raise RoundError("invalid %s JSON" % label) from exc


def validate_spec(raw, cwd):
    top = ("schema", "round_id", "hypothesis", "primary_metric", "created_at", "context",
           "inputs", "cases", "arms", "strata", "comparisons", "order", "budgets",
           "opening", "qualifications", "lineage")
    object_shape(raw, top, "manifest")
    require(raw["schema"] == SCHEMA, "unsupported schema")
    for key in ("round_id", "hypothesis", "primary_metric", "created_at"):
        nonempty(raw[key], key)
    context_keys = ("repo", "checkout", "workspace", "records", "procedure", "runtime", "binding_reference")
    object_shape(raw["context"], context_keys, "context")
    for key in context_keys:
        nonempty(raw["context"][key], "context." + key)
    for key in ("repo", "checkout", "workspace"):
        require(Path(raw["context"][key]).is_absolute(), "context.%s must be absolute" % key)
    contained_dir(cwd, raw["context"]["records"], "context.records")

    require(type(raw["inputs"]) is list and raw["inputs"], "inputs must be a nonempty array")
    inputs = {}
    for row in raw["inputs"]:
        object_shape(row, ("id", "sha256", "kind", "path"), "input")
        key = ident(row["id"], "input.id")
        require(key not in inputs, "duplicate input id")
        require(type(row["sha256"]) is str and HASH_RE.fullmatch(row["sha256"]) is not None,
                "input sha256 is invalid")
        if row["kind"] == "public-local":
            contained_file(cwd, row["path"], "public input", row["sha256"])
        elif row["kind"] == "opaque":
            require(row["path"] is None, "opaque input path must be null")
        else:
            raise RoundError("unsupported input kind")
        inputs[key] = row

    require(type(raw["cases"]) is list and raw["cases"], "cases must be a nonempty array")
    case_ids = []
    for row in raw["cases"]:
        object_shape(row, ("case_id", "input_id", "oracle_id"), "case")
        case_id = ident(row["case_id"], "case_id")
        require(case_id not in case_ids, "duplicate case id")
        require(row["input_id"] in inputs and row["oracle_id"] in inputs, "case references unknown input")
        require(inputs[row["oracle_id"]]["kind"] == "opaque", "oracle input must be opaque")
        case_ids.append(case_id)
    require(type(raw["arms"]) is list and raw["arms"], "arms must be nonempty")
    arms = [ident(item, "arm") for item in raw["arms"]]
    require(len(arms) == len(set(arms)), "duplicate arm")

    require(type(raw["strata"]) is list and raw["strata"], "strata must be nonempty")
    strata = {}
    for row in raw["strata"]:
        object_shape(row, ("id", "capability", "effort", "support", "binding_input_id"), "stratum")
        key = ident(row["id"], "stratum.id")
        require(key not in strata, "duplicate stratum")
        require(row["capability"] in ("high", "medium", "low"), "invalid capability")
        require(row["effort"] in ("low", "medium", "high", "max"), "invalid effort")
        require(row["support"] in ("supported", "unsupported", "unknown"), "invalid support")
        require(row["binding_input_id"] in inputs, "stratum binding input unknown")
        strata[key] = row

    require(type(raw["comparisons"]) is list and raw["comparisons"], "comparisons must be nonempty")
    comparisons = {}
    for row in raw["comparisons"]:
        object_shape(row, ("id", "baseline_arm", "candidate_arm", "decision_rule"), "comparison")
        key = ident(row["id"], "comparison.id")
        require(key not in comparisons, "duplicate comparison")
        require(row["baseline_arm"] in arms and row["candidate_arm"] in arms and
                row["baseline_arm"] != row["candidate_arm"], "comparison arms invalid")
        rule = row["decision_rule"]
        require(type(rule) is dict and rule.get("name") == "paired-count/1", "unsupported decision rule")
        allowed = {"name", "n_min", "win_min", "defect_reduction_min", "max_time_ratio",
                   "max_additional_judgment_wait_ms"}
        require(set(rule) <= allowed and {"name", "n_min", "win_min", "defect_reduction_min"} <= set(rule),
                "decision rule shape invalid")
        for name in ("n_min", "win_min", "defect_reduction_min"):
            integer(rule[name], "decision_rule." + name, 1)
        if "max_time_ratio" in rule:
            ratio = rule["max_time_ratio"]
            object_shape(ratio, ("numerator", "denominator"), "max_time_ratio")
            integer(ratio["numerator"], "ratio numerator", 1)
            integer(ratio["denominator"], "ratio denominator", 1)
        if "max_additional_judgment_wait_ms" in rule:
            integer(rule["max_additional_judgment_wait_ms"], "wait cap")
        comparisons[key] = row

    require(type(raw["budgets"]) is dict and raw["budgets"], "budgets must be an object")
    dims = {}
    for key, row in raw["budgets"].items():
        ident(key, "budget dimension")
        object_shape(row, ("unit", "limit"), "budget")
        nonempty(row["unit"], "budget unit")
        integer(row["limit"], "budget limit")
        dims[key] = row
    require(set(DIMENSIONS) <= set(dims), "initial budget dimensions are required")

    require(type(raw["order"]) is list, "order must be an array")
    order = {}
    order_unique = set()
    pair_arms = set()
    for row in raw["order"]:
        object_shape(row, ("unit_id", "stage", "case_id", "arm", "stratum", "reservation"), "order row")
        uid = ident(row["unit_id"], "unit_id")
        require(uid not in order, "duplicate unit id")
        require(row["stage"] in ("smoke", "measurement"), "invalid stage")
        require(row["case_id"] in case_ids and row["arm"] in arms and row["stratum"] in strata,
                "order row references unknown case/arm/stratum")
        unique = (row["stage"], row["case_id"], row["stratum"], row["arm"])
        require(unique not in order_unique, "duplicate stage/case/stratum/arm")
        order_unique.add(unique)
        object_shape(row["reservation"], dims.keys(), "reservation")
        for dim, value in row["reservation"].items():
            integer(value, "reservation." + dim)
        require(row["reservation"].get("episodes") == 1, "each unit reserves exactly one episode")
        order[uid] = row
        if row["stage"] == "measurement":
            pair_arms.add((row["case_id"], row["stratum"], row["arm"]))
    seen_measurement = False
    for row in raw["order"]:
        if row["stage"] == "measurement":
            seen_measurement = True
        else:
            require(not seen_measurement, "smoke rows must precede measurement rows")
    for comparison in comparisons.values():
        rule = comparison["decision_rule"]
        for stratum in strata:
            planned = {case for case, s, arm in pair_arms
                       if s == stratum and (case, s, comparison["baseline_arm"]) in pair_arms
                       and (case, s, comparison["candidate_arm"]) in pair_arms}
            require(len(planned) >= rule["n_min"], "planned measurement pairs below n_min")

    require(type(raw["qualifications"]) is list, "qualifications must be an array")
    quals = set()
    for row in raw["qualifications"]:
        object_shape(row, ("id", "procedure_input_id"), "qualification requirement")
        key = ident(row["id"], "qualification.id")
        require(key not in quals and row["procedure_input_id"] in inputs, "invalid qualification reference")
        quals.add(key)

    opening = raw["opening"]
    # An owner-authorized replacement of a stopped round may add an optional extension receipt.
    extended = type(opening) is dict and "extension_receipt" in opening
    object_shape(opening, ("reserved", "known_consumed", "unknown", "corrections",
                           "parent_receipt", "new_allocation_receipt") + (("extension_receipt",) if extended else ()),
                 "opening")
    for field in ("reserved", "known_consumed", "unknown"):
        object_shape(opening[field], dims.keys(), "opening." + field)
        for key, value in opening[field].items():
            if field == "known_consumed" and value is None:
                continue
            integer(value, "opening.%s.%s" % (field, key))
    integer(opening["corrections"], "opening.corrections")
    lineage = raw["lineage"]
    object_shape(lineage, ("budget_pool_id", "parent_result"), "lineage")
    ident(lineage["budget_pool_id"], "budget_pool_id")
    parent = lineage["parent_result"]
    if parent is None:
        require(not extended, "an extension receipt requires a parent result")
        require(opening["parent_receipt"] is None and opening["new_allocation_receipt"] is not None,
                "new allocation requires its receipt and no parent")
        ref_check(cwd, opening["new_allocation_receipt"], "new allocation receipt")
        for field in ("reserved", "unknown"):
            require(all(value == 0 for value in opening[field].values()), "new allocation opening must be zero")
        require(all(value in (0, None) for value in opening["known_consumed"].values()) and opening["corrections"] == 0,
                "new allocation cannot carry prior consumption or corrections")
    else:
        require(opening["parent_receipt"] is not None and opening["new_allocation_receipt"] is None,
                "inherited allocation requires parent receipt only")
        parent_result = canonical_ref(cwd, parent, "parent result")
        ref_check(cwd, opening["parent_receipt"], "parent receipt")
        require(opening["parent_receipt"] == parent, "parent receipt identity must match parent result")
        require(parent_result.get("schema") == RESULT_SCHEMA and parent_result.get("lineage", {}).get("budget_pool_id") == lineage["budget_pool_id"],
                "parent result pool/schema mismatch")
        summary = parent_result.get("summary", {})
        require(summary.get("reserved") == opening["reserved"] and
                summary.get("known_consumed") == opening["known_consumed"] and
                summary.get("unknown") == opening["unknown"] and
                summary.get("corrections") == opening["corrections"], "opening does not match parent summary")
        parent_budgets = parent_result.get("budgets")
        require(type(parent_budgets) is dict and set(parent_budgets) == set(dims),
                "parent budget dimensions mismatch")
        if extended:
            ref_check(cwd, opening["extension_receipt"], "extension receipt")
        for key, row in dims.items():
            parent_budget = parent_budgets[key]
            require(type(parent_budget) is dict and type(parent_budget.get("limit")) is int and
                    parent_budget.get("unit") == row["unit"], "parent budget unit/limit mismatch")
            # Without an extension the child keeps the parent's exact limits; with one, a limit may only grow.
            if extended:
                require(row["limit"] >= parent_budget["limit"], "an extension cannot lower a parent limit")
            else:
                require(parent_budget["limit"] == row["limit"], "parent budget unit/limit mismatch")

    # Opening commitments cannot already exceed any finite limit.
    for key, row in dims.items():
        require(opening["reserved"][key] <= row["limit"], "opening reservation exceeds limit")
    return raw


def connect(db, readonly=False):
    if readonly:
        uri = Path(db).resolve().as_uri() + "?mode=ro"
        try:
            return sqlite3.connect(uri, uri=True, timeout=0)
        except sqlite3.Error as exc:
            raise RoundError("round store unavailable", 3) from exc
    try:
        return sqlite3.connect(db, timeout=0)
    except sqlite3.OperationalError as exc:
        raise RoundError("round store busy or unavailable", 3) from exc


def db_init(db, manifest_bytes):
    con = connect(db)
    try:
        con.execute("PRAGMA journal_mode=DELETE")
        con.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value BLOB NOT NULL)")
        con.execute("CREATE TABLE events (sequence INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL, previous_sha256 TEXT NOT NULL, body_json BLOB NOT NULL, sha256 TEXT NOT NULL)")
        con.execute("INSERT INTO metadata(key,value) VALUES('manifest',?)", (manifest_bytes,))
        con.commit()
    except sqlite3.Error as exc:
        con.rollback()
        raise RoundError("cannot initialize round database: %s" % exc, 3) from exc
    finally:
        con.close()


def load_manifest(round_path, con):
    try:
        row = con.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()
        require(row is not None, "round manifest missing")
        data = bytes(row[0])
        manifest = _loads(data, "stored manifest")
        require(canonical(manifest) == data, "stored manifest is not canonical")
        seal = manifest.get("seal_sha256")
        unsigned = dict(manifest)
        unsigned.pop("seal_sha256", None)
        require(type(seal) is str and HASH_RE.fullmatch(seal) and digest(canonical(unsigned)) == seal,
                "round seal mismatch")
        expected = (round_path / "manifest.json").read_bytes()
        require(expected == data, "manifest copy does not match sealed store")
        return manifest
    except sqlite3.Error as exc:
        raise RoundError("round store unavailable", 3) from exc


def event_rows(con, manifest):
    try:
        rows = con.execute("SELECT sequence,event_id,previous_sha256,body_json,sha256 FROM events ORDER BY sequence").fetchall()
    except sqlite3.Error as exc:
        raise RoundError("round store unavailable", 3) from exc
    previous = manifest["seal_sha256"]
    parsed, seen = [], set()
    for expected_seq, row in enumerate(rows, 1):
        seq, event_id, prev, body_bytes, stored_hash = row
        require(seq == expected_seq and prev == previous, "event chain sequence/predecessor mismatch")
        body_bytes = bytes(body_bytes)
        event = _loads(body_bytes, "event")
        require(canonical(event) == body_bytes, "event body is not canonical")
        require(event.get("event_id") == event_id and event_id not in seen, "event identity mismatch")
        envelope = dict(sequence=seq, previous_sha256=prev, event=event)
        calculated = digest(canonical(envelope))
        require(calculated == stored_hash, "event chain hash mismatch")
        previous = calculated
        seen.add(event_id)
        parsed.append((seq, event, calculated))
    return parsed, previous


def validate_event(event, manifest):
    object_shape(event, ("event_id", "kind", "seal_sha256", "recorded_at", "actor", "unit_id", "payload"), "event")
    ident(event["event_id"], "event_id")
    require(event["kind"] in ("qualification", "start", "finish", "reconcile", "stop"), "unknown event kind")
    require(event["seal_sha256"] == manifest["seal_sha256"], "event seal mismatch")
    nonempty(event["recorded_at"], "recorded_at")
    nonempty(event["actor"], "actor")
    require(type(event["payload"]) is dict, "event payload must be an object")
    kind = event["kind"]
    if kind == "qualification":
        require(event["unit_id"] is None, "qualification unit must be null")
        p = event["payload"]
        object_shape(p, ("id", "status", "receipt"), "qualification payload")
        require(any(q["id"] == p["id"] for q in manifest["qualifications"]), "unknown qualification")
        require(p["status"] in ("pass", "fail", "unavailable"), "invalid qualification status")
    elif kind == "start":
        require(event["unit_id"] is not None, "start requires unit")
        ident(event["unit_id"], "unit_id")
        object_shape(event["payload"], (), "start payload")
    elif kind in ("finish", "reconcile"):
        require(event["unit_id"] is not None, "terminal event requires unit")
        ident(event["unit_id"], "unit_id")
        p = event["payload"]
        keys = ("status", "usage", "scores", "receipt", "corrections_delta")
        if kind == "reconcile":
            keys += ("prior_event_sha256",)
        object_shape(p, keys, kind + " payload")
        require(p["status"] in ("success", "failed", "infrastructure-failure", "aborted", "unknown"), "invalid terminal status")
        object_shape(p["usage"], manifest["budgets"].keys(), "usage")
        for key, value in p["usage"].items():
            if value is not None:
                integer(value, "usage." + key)
        if p["scores"] is not None:
            score = p["scores"]
            object_shape(score, ("correct", "safety", "defects", "wall_ms", "additional_judgment_wait_ms"), "scores")
            require(type(score["correct"]) is bool, "scores.correct must be boolean")
            require(score["safety"] in ("preserved", "violated", "unknown"), "invalid safety score")
            integer(score["defects"], "scores.defects")
            for key in ("wall_ms", "additional_judgment_wait_ms"):
                if score[key] is not None:
                    integer(score[key], "scores." + key)
        else:
            require(p["status"] == "unknown", "only unknown status may omit scores")
        ref_check(Path.cwd(), p["receipt"], "terminal receipt")
        integer(p["corrections_delta"], "corrections_delta")
        if kind == "reconcile":
            require(type(p["prior_event_sha256"]) is str and HASH_RE.fullmatch(p["prior_event_sha256"]), "reconcile prior hash invalid")
    else:
        require(event["unit_id"] is None, "stop unit must be null")
        object_shape(event["payload"], ("reason", "state", "receipt"), "stop payload")
        nonempty(event["payload"]["reason"], "stop reason")
        require(event["payload"]["state"] in ("aborted", "infrastructure-failure", "inconclusive"), "invalid stop state")
        ref_check(Path.cwd(), event["payload"]["receipt"], "stop receipt")
    if kind == "qualification":
        ref_check(Path.cwd(), event["payload"]["receipt"], "qualification receipt")


def terminal_has_unknown_fields(payload):
    scores = payload["scores"]
    return (payload["status"] == "unknown" or
            any(value is None for value in payload["usage"].values()) or
            scores is None or
            any(value is None or (key == "safety" and value == "unknown")
                for key, value in scores.items()))


def fold_events(manifest, events):
    order = manifest["order"]
    order_by_id = {row["unit_id"]: row for row in order}
    started, terminals, qualifications = {}, {}, {}
    stop = None
    blocked = False
    infra = False
    safety = False
    corrections = manifest["opening"]["corrections"]
    for seq, event, event_hash in events:
        validate_event(event, manifest)
        kind = event["kind"]
        p = event["payload"]
        if kind == "qualification":
            qid = p["id"]
            require(not started, "qualification must precede the first start")
            require(qid not in qualifications, "qualification is immutable")
            qualifications[qid] = (p["status"], p["receipt"])
            continue
        if kind == "start":
            uid = event["unit_id"]
            require(uid in order_by_id, "start references undeclared unit")
            require(uid not in started, "unit already started")
            require(stop is None and not blocked and not infra and not safety, "round is terminal or blocked")
            require(all(qualifications.get(q["id"], (None,))[0] == "pass" for q in manifest["qualifications"]),
                    "qualification requirements are not all passed")
            require(len(started) < len(order), "no pending sealed unit")
            expected = order[len(started)]["unit_id"]
            require(uid == expected, "start is out of sealed order")
            require(not any(u not in terminals for u in started), "previous unit has no terminal observation")
            totals = {dim: manifest["opening"]["reserved"][dim] for dim in manifest["budgets"]}
            for unit in started.values():
                for dim, amount in unit["reservation"].items():
                    totals[dim] += amount
            for dim, amount in order_by_id[uid]["reservation"].items():
                require(totals[dim] + amount <= manifest["budgets"][dim]["limit"], "reservation exceeds budget")
            started[uid] = {"event": event, "hash": event_hash, "reservation": order_by_id[uid]["reservation"]}
        elif kind == "finish":
            uid = event["unit_id"]
            require(uid in started and uid not in terminals, "finish requires one active unit")
            terminals[uid] = {"event": event, "hash": event_hash, "unknown": p["status"] == "unknown"}
            corrections += p["corrections_delta"]
            if p["status"] == "infrastructure-failure":
                infra = True
            if p["scores"] is not None and p["scores"]["safety"] == "violated":
                safety = True
            if any(p["usage"][key] is not None and p["usage"][key] > started[uid]["reservation"][key]
                   for key in p["usage"]):
                infra = True
        elif kind == "reconcile":
            uid = event["unit_id"]
            require(uid in terminals and terminal_has_unknown_fields(terminals[uid]["event"]["payload"]),
                    "reconcile requires an unknown terminal field")
            require(terminals[uid]["hash"] == p["prior_event_sha256"], "reconcile prior event mismatch")
            # Only unknown facts are replaced. Reconciliation corrections are additive.
            prior = terminals[uid]["event"]["payload"]
            require(p["status"] != "unknown" if prior["status"] == "unknown" else p["status"] == prior["status"],
                    "reconcile must resolve unknown status without changing known status")
            require(p["scores"] is not None, "reconcile must supply observed scores")
            require(all(prior["usage"][key] is None or prior["usage"][key] == p["usage"][key]
                        for key in prior["usage"]), "reconcile changes known usage")
            if prior["scores"] is not None:
                for key, value in prior["scores"].items():
                    if value is not None and not (key == "safety" and value == "unknown"):
                        require(p["scores"][key] == value, "reconcile changes known scores." + key)
            terminals[uid] = {"event": event, "hash": event_hash, "unknown": False,
                              "reconciled_from": prior}
            corrections += p["corrections_delta"]
            if p["status"] == "infrastructure-failure":
                infra = True
            if p["scores"]["safety"] == "violated":
                safety = True
            if any(p["usage"][key] is not None and p["usage"][key] > started[uid]["reservation"][key]
                   for key in p["usage"]):
                infra = True
        elif kind == "stop":
            require(stop is None, "round already stopped")
            stop = p
            if p["state"] == "infrastructure-failure":
                infra = True
        # Resolve only current uncertainty; known violations above stay latched.
        blocked = any(item["unknown"] or
                      any(value is None for value in item["event"]["payload"]["usage"].values()) or
                      (item["event"]["payload"]["scores"] is not None and
                       item["event"]["payload"]["scores"]["safety"] == "unknown")
                      for item in terminals.values())
    infra = infra or blocked
    return {"started": started, "terminals": terminals, "qualifications": qualifications,
            "stop": stop, "blocked": blocked, "infra": infra, "safety": safety,
            "corrections": corrections}


def receipt(operation, state, seal, **extra):
    return {"schema": RECEIPT_SCHEMA, "operation": operation, "state": state,
            "seal_sha256": seal, **extra}


def emit(value):
    sys.stdout.buffer.write(canonical(value))
    sys.stdout.buffer.flush()


def seal(spec_path, round_arg):
    cwd = Path.cwd()
    raw = read_json(spec_path)
    validate_spec(raw, cwd)
    destination = Path(round_arg)
    if not destination.is_absolute():
        destination = cwd / destination
    destination = destination.absolute()
    require(not destination.exists() and not destination.is_symlink(), "round destination already exists")
    require(destination.parent.resolve() == cwd.resolve() or cwd.resolve() in destination.parent.resolve().parents,
            "round destination must be below cwd")
    unsigned = dict(raw)
    seal_hash = digest(canonical(unsigned))
    manifest = {**unsigned, "seal_sha256": seal_hash}
    try:
        destination.mkdir(parents=False, exist_ok=False)
        data = canonical(manifest)
        (destination / "manifest.json").write_bytes(data)
        db_init(destination / "round.sqlite", data)
    except FileExistsError as exc:
        raise RoundError("round destination already exists") from exc
    except OSError as exc:
        raise RoundError("cannot create round: %s" % exc, 3) from exc
    emit(receipt("seal", "sealed", seal_hash))
    return 0


def open_round(round_arg, readonly):
    cwd = Path.cwd().resolve()
    supplied = Path(round_arg)
    if not supplied.is_absolute():
        supplied = cwd / supplied
    path = contained_dir(cwd, str(supplied), "round directory")
    require(path != cwd, "round directory must be below cwd")
    for name in ("manifest.json", "round.sqlite"):
        contained_file(cwd, (path / name).relative_to(cwd).as_posix(), "round " + name)
    for suffix in ("-journal", "-wal", "-shm"):
        member = path / ("round.sqlite" + suffix)
        if member.exists() or member.is_symlink():
            contained_file(cwd, member.relative_to(cwd).as_posix(), "round store sidecar")
    con = connect(path / "round.sqlite", readonly)
    try:
        manifest = load_manifest(path, con)
        for row in manifest["inputs"]:
            if row["kind"] == "public-local":
                contained_file(cwd, row["path"], "public input", row["sha256"])
        return path, con, manifest
    except Exception:
        con.close()
        raise


def record(round_arg, event_path):
    path, con, manifest = open_round(round_arg, False)
    try:
        event = read_json(event_path)
        con.execute("BEGIN IMMEDIATE")
        existing, head = event_rows(con, manifest)
        validate_event(event, manifest)
        prior = next((row for row in existing if row[1]["event_id"] == event["event_id"]), None)
        if prior:
            require(canonical(prior[1]) == canonical(event), "event id conflicts with retained event")
            seq, old, event_hash = prior
            con.rollback()
            emit(receipt("record", "already-recorded", manifest["seal_sha256"],
                         event_sha256=event_hash, sequence=seq, dispatch_allowed=False))
            return 0
        folded = fold_events(manifest, existing)
        # Validate transition and public receipt facts before insertion.
        candidate_hash = digest(canonical(dict(sequence=len(existing)+1, previous_sha256=head, event=event)))
        fold_events(manifest, existing + [(len(existing)+1, event, candidate_hash)])
        seq = len(existing) + 1
        con.execute("INSERT INTO events(sequence,event_id,previous_sha256,body_json,sha256) VALUES(?,?,?,?,?)",
                    (seq, event["event_id"], head, canonical(event), candidate_hash))
        con.commit()
        dispatch = event["kind"] == "start"
        con.close()
        emit(receipt("record", "recorded", manifest["seal_sha256"], event_sha256=candidate_hash,
                     sequence=seq, dispatch_allowed=dispatch))
        return 0
    except sqlite3.OperationalError as exc:
        try: con.rollback()
        except sqlite3.Error: pass
        raise RoundError("round store busy or unavailable", 3) from exc
    except sqlite3.Error as exc:
        try: con.rollback()
        except sqlite3.Error: pass
        raise RoundError("round store error: %s" % exc, 3) from exc
    finally:
        try: con.close()
        except Exception: pass


def read_state(round_arg):
    path, con, manifest = open_round(round_arg, True)
    try:
        events, head = event_rows(con, manifest)
        folded = fold_events(manifest, events)
        return path, manifest, events, head, folded
    finally:
        con.close()


def result_for(manifest, events, head, folded):
    started = folded["started"]
    terminals = folded["terminals"]
    qual_rows = []
    for row in manifest["qualifications"]:
        status, ref_value = folded["qualifications"].get(row["id"], ("unknown", None))
        qual_rows.append({"id": row["id"], "status": status, "receipt": ref_value})
    budget_rows, summary = {}, {"reserved": {}, "known_consumed": {}, "unknown": {},
                                "corrections": folded["corrections"]}
    for dim, spec_row in manifest["budgets"].items():
        opening = manifest["opening"]
        started_reserved = sum(item["reservation"][dim] for item in started.values())
        active = sum(item["reservation"][dim] for uid, item in started.items() if uid not in terminals)
        unknown_reserved = sum(started[uid]["reservation"][dim] for uid, terminal in terminals.items()
                               if terminal["unknown"] or terminal["event"]["payload"]["usage"][dim] is None)
        known_values = []
        for uid, terminal in terminals.items():
            p = terminal["event"]["payload"]
            value = p["usage"][dim]
            if value is not None and not terminal["unknown"]:
                known_values.append(value)
        opening_known = opening["known_consumed"][dim]
        known = None if opening_known is None else opening_known + sum(known_values)
        unknown = opening["unknown"][dim] + active + unknown_reserved
        reserved = opening["reserved"][dim] + started_reserved
        budget_rows[dim] = {"unit": spec_row["unit"], "limit": spec_row["limit"],
                            "opening_reserved": opening["reserved"][dim],
                            "started_reserved": started_reserved, "known_consumed": known,
                            "active_reserved": active, "unknown_reserved": unknown_reserved,
                            "remaining": spec_row["limit"] - reserved}
        summary["reserved"][dim] = reserved
        summary["known_consumed"][dim] = known
        summary["unknown"][dim] = unknown

    # Build only required measurement pairs; smoke and one-sided rows remain explicit exclusions.
    order_by_key = {}
    for row in manifest["order"]:
        order_by_key[(row["stage"], row["case_id"], row["stratum"], row["arm"])] = row
    pair_rows, exclusions = [], []
    comparisons = []
    any_missing = False
    any_unknown = False
    pending = len(started) < len(manifest["order"]) and folded["stop"] is None
    by_id = {row["unit_id"]: row for row in manifest["order"]}
    for comp in manifest["comparisons"]:
        base, cand = comp["baseline_arm"], comp["candidate_arm"]
        for stratum in manifest["strata"]:
            relevant = []
            for row in manifest["order"]:
                if row["stratum"] != stratum["id"] or row["arm"] not in (base, cand):
                    continue
                if row["stage"] == "smoke":
                    exclusions.append({"comparison_id": comp["id"], "stratum_id": stratum["id"],
                                       "case_id": row["case_id"], "unit_id": row["unit_id"], "reason": "smoke"})
            case_set = sorted({row["case_id"] for row in manifest["order"]
                               if row["stage"] == "measurement" and row["stratum"] == stratum["id"] and row["arm"] in (base, cand)})
            valid_count = wins = losses = both_correct = both_incorrect = 0
            missing_cases, btimes, ctimes, bdef, cdef = [], [], [], [], []
            local_missing = False
            for case_id in case_set:
                b = order_by_key.get(("measurement", case_id, stratum["id"], base))
                c = order_by_key.get(("measurement", case_id, stratum["id"], cand))
                if b is None or c is None:
                    row = b or c
                    exclusions.append({"comparison_id": comp["id"], "stratum_id": stratum["id"],
                                       "case_id": case_id, "unit_id": row["unit_id"],
                                       "reason": "unpaired-measurement"})
                    continue
                bt = terminals.get(b["unit_id"])
                ct = terminals.get(c["unit_id"])
                bs = bt["event"]["payload"]["scores"] if bt and not bt["unknown"] else None
                cs = ct["event"]["payload"]["scores"] if ct and not ct["unknown"] else None
                if bt is None or ct is None:
                    status = "missing"
                elif bs is None or cs is None:
                    status = "unknown"
                else:
                    req = comp["decision_rule"]
                    facts = [bs["correct"], cs["correct"], bs["safety"], cs["safety"], bs["defects"], cs["defects"]]
                    if "max_time_ratio" in req:
                        facts.extend((bs["wall_ms"], cs["wall_ms"]))
                    if "max_additional_judgment_wait_ms" in req:
                        facts.extend((bs["additional_judgment_wait_ms"], cs["additional_judgment_wait_ms"]))
                    status = "complete" if all(x is not None and x != "unknown" for x in facts) else "unknown"
                if status != "complete":
                    local_missing = True
                    missing_cases.append(case_id)
                    any_missing = any_missing or status == "missing"
                    any_unknown = any_unknown or status == "unknown"
                else:
                    valid_count += 1
                    if cs["correct"] and not bs["correct"]: wins += 1
                    elif bs["correct"] and not cs["correct"]: losses += 1
                    elif bs["correct"] and cs["correct"]: both_correct += 1
                    else: both_incorrect += 1
                    bdef.append(bs["defects"]); cdef.append(cs["defects"])
                    if bs["wall_ms"] is not None: btimes.append(bs["wall_ms"])
                    if cs["wall_ms"] is not None: ctimes.append(cs["wall_ms"])
                pair_rows.append({"comparison_id": comp["id"], "stratum_id": stratum["id"],
                                  "case_id": case_id, "status": status,
                                  "baseline_unit": b["unit_id"], "candidate_unit": c["unit_id"],
                                  "baseline": bs, "candidate": cs})
            required_count = sum(1 for case_id in case_set
                                 if order_by_key.get(("measurement", case_id, stratum["id"], base)) is not None
                                 and order_by_key.get(("measurement", case_id, stratum["id"], cand)) is not None)
            rule = comp["decision_rule"]
            if folded["safety"]:
                decision = "reject"
            elif folded["infra"] or local_missing or valid_count < rule["n_min"]:
                decision = "inconclusive"
            elif losses > 0:
                decision = "reject"
            else:
                benefit = wins >= rule["win_min"] or sum(bdef) - sum(cdef) >= rule["defect_reduction_min"]
                overhead_reject = False
                overhead_unknown = False
                if "max_time_ratio" in rule:
                    if len(btimes) != valid_count or len(ctimes) != valid_count:
                        overhead_unknown = True
                    else:
                        numerator = rule["max_time_ratio"]["numerator"]
                        denominator = rule["max_time_ratio"]["denominator"]
                        total_b, total_c = sum(btimes), sum(ctimes)
                        if total_b == 0 and total_c > 0:
                            overhead_reject = True
                        elif total_c * denominator > total_b * numerator:
                            overhead_reject = True
                if "max_additional_judgment_wait_ms" in rule:
                    for pair in pair_rows:
                        if pair["comparison_id"] == comp["id"] and pair["stratum_id"] == stratum["id"] and pair["status"] == "complete":
                            if pair["candidate"]["additional_judgment_wait_ms"] is None:
                                overhead_unknown = True
                            elif pair["candidate"]["additional_judgment_wait_ms"] > rule["max_additional_judgment_wait_ms"]:
                                overhead_reject = True
                if overhead_reject:
                    decision = "reject"
                elif overhead_unknown:
                    decision = "inconclusive"
                elif benefit:
                    decision = "supported"
                else:
                    decision = "tie"
            comparisons.append({"comparison_id": comp["id"], "stratum_id": stratum["id"],
                                "decision": decision, "decision_rule": comp["decision_rule"],
                                "valid_count": valid_count, "required_count": required_count,
                                "win_count": wins, "loss_count": losses,
                                "both_correct": both_correct, "both_incorrect": both_incorrect,
                                "missing_cases": sorted(set(missing_cases)),
                                "wall_ms": {"baseline": sum(btimes) if len(btimes) == valid_count else None,
                                            "candidate": sum(ctimes) if len(ctimes) == valid_count else None},
                                "defects": {"baseline": sum(bdef) if len(bdef) == valid_count else None,
                                            "candidate": sum(cdef) if len(cdef) == valid_count else None}})

    exclusions.sort(key=lambda x: (x["comparison_id"], x["stratum_id"], x["case_id"], x["unit_id"]))
    reasons = []
    if folded["infra"]: reasons.append("infrastructure-failure")
    if folded["safety"]: reasons.append("safety-violation")
    if folded["stop"]: reasons.append("explicit-stop:" + folded["stop"]["reason"])
    if any(row["decision"] in ("tie", "inconclusive") for row in comparisons): reasons.append("comparison-inconclusive")
    if not started: round_state = folded["stop"]["state"] if folded["stop"] else "not-run"
    elif folded["infra"]: round_state = "infrastructure-failure"
    elif folded["stop"] and folded["stop"]["state"] == "infrastructure-failure": round_state = "infrastructure-failure"
    elif folded["stop"] and folded["stop"]["state"] == "aborted": round_state = "aborted"
    elif folded["safety"]: round_state = "aborted"
    elif pending: round_state = "running"
    elif folded["stop"] and folded["stop"]["state"] == "inconclusive": round_state = "inconclusive"
    elif any(row["decision"] in ("inconclusive", "tie") for row in comparisons): round_state = "inconclusive"
    else: round_state = "success"
    result = {"schema": RESULT_SCHEMA, "seal_sha256": manifest["seal_sha256"],
              "event_head_sha256": head, "round_state": round_state, "reasons": reasons,
              "comparisons": comparisons, "pairs": pair_rows, "exclusions": exclusions,
              "budgets": budget_rows, "qualifications": qual_rows,
              "lineage": manifest["lineage"], "summary": summary}
    return result


def make_output(out_arg, evidence_root):
    out = Path(out_arg)
    if not out.is_absolute(): out = Path.cwd() / out
    out = out.absolute()
    require(not out.exists() and not out.is_symlink(), "output already exists")
    try:
        out.resolve().relative_to(evidence_root.resolve())
        raise RoundError("output must be disjoint from evidence tree")
    except ValueError:
        pass
    try:
        evidence_root.resolve().relative_to(out.resolve())
        raise RoundError("output must be disjoint from evidence tree")
    except ValueError:
        pass
    require(out.parent.resolve() == Path.cwd().resolve() or Path.cwd().resolve() in out.parent.resolve().parents,
            "output must be below cwd")
    try:
        out.mkdir(parents=False, exist_ok=False)
    except OSError as exc:
        raise RoundError("cannot create output: %s" % exc, 3) from exc
    return out


def compute(round_arg, output_arg):
    path, manifest, events, head, folded = read_state(round_arg)
    out = make_output(output_arg, path)
    result = result_for(manifest, events, head, folded)
    data = canonical(result)
    (out / "result.json").write_bytes(data)
    emit(receipt("compute", "computed", manifest["seal_sha256"], result_sha256=digest(data)))
    return 0 if result["round_state"] == "success" else 1


def replay(round_arg, against_arg, output_arg):
    path, manifest, events, head, folded = read_state(round_arg)
    expected_path = Path(against_arg)
    expected_bytes = expected_path.read_bytes()
    expected_obj = _loads(expected_bytes, "expected result")
    require(canonical(expected_obj) == expected_bytes, "expected result must be canonical")
    require(type(expected_obj) is dict and expected_obj.get("schema") == RESULT_SCHEMA and
            expected_obj.get("seal_sha256") == manifest["seal_sha256"] and
            expected_obj.get("event_head_sha256") == head,
            "expected result identity mismatch")
    out = make_output(output_arg, path)
    data = canonical(result_for(manifest, events, head, folded))
    (out / "result.json").write_bytes(data)
    matched = expected_bytes == data
    emit(receipt("replay", "matched" if matched else "mismatch", manifest["seal_sha256"],
                 result_sha256=digest(data)))
    return 0 if matched and _loads(data, "result")["round_state"] == "success" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="evaluation_rounds.py")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("seal"); p.add_argument("--spec", required=True); p.add_argument("--round", required=True)
    p = sub.add_parser("record"); p.add_argument("--round", required=True); p.add_argument("--event", required=True)
    p = sub.add_parser("compute"); p.add_argument("--round", required=True); p.add_argument("--output", required=True)
    p = sub.add_parser("replay"); p.add_argument("--round", required=True); p.add_argument("--against", required=True); p.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "seal": return seal(args.spec, args.round)
        if args.command == "record": return record(args.round, args.event)
        if args.command == "compute": return compute(args.round, args.output)
        return replay(args.round, args.against, args.output)
    except RoundError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    except sqlite3.OperationalError as exc:
        print("round store busy or unavailable: %s" % exc, file=sys.stderr)
        return 3
    except OSError as exc:
        print("I/O error: %s" % exc, file=sys.stderr)
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
