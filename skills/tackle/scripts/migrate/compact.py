#!/usr/bin/env python3
"""Installed, bounded Tackle compact migration route."""
from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import signal

# ``python -I`` removes the script directory from sys.path.  The shipped adapters
# are intentionally siblings and all must share this one schema module instance.
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
import schema
import step_pre3_to_3
import step_3_to_4
import step_4_to_5
from context_bundle import Context
from lint_runner import canonical_rows, lint_verdict
from decompose_check import task_fields

CATALOG_NAME = "migration-catalog.json"
CATALOG_SCHEMA = "tackle-migration-catalog/1"
PLAN_SCHEMA = "tackle-migration-plan/1"
JOB_SCHEMA = "tackle-migration-job/1"
FAMILIES = ("I", "P", "S", "A", "R", "B", "M", "E", "J", "H", "N", "Q", "W", "O", "V", "Z")
REQUIRED = frozenset(set(FAMILIES) - {"J", "W", "O"})
RULE_KEYS = {"id", "kind", "detector", "applies", "requires", "effect", "postcondition", "recovery", "instructions", "provenance_ids", "exceptions"}
TOP_KEYS = {"schema", "revision", "target_methodology", "supported_buckets", "rules", "provenance"}
APPLIES = {"I": "always", "P": "active", "S": "structure", "A": "structure", "R": "active", "B": "next-wave", "M": "active", "E": "active", "J": "requested", "H": "active", "N": "multi-repo", "Q": "current-consumer", "W": "requested", "O": "requested", "V": "active", "Z": "active"}
FAMILY_COUNTS = {"I": 8, "P": 17, "S": 7, "A": 16, "R": 7, "B": 38, "M": 11, "E": 31, "J": 3, "H": 6, "N": 1, "Q": 2, "W": 5, "O": 12, "V": 17, "Z": 39}
CONTEXT_KEYS = {"workspace", "target", "next_wave", "boundary", "optional_requests", "date", "run_id"}

class MigrationError(ValueError):
    pass

class PendingError(MigrationError):
    """A well-formed operation that must wait for evidence, a writer, or conflict resolution."""
    pass

def _canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")

def _sha(data):
    return hashlib.sha256(data).hexdigest()

def _read_json(path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise MigrationError("duplicate-json-key:" + key)
            out[key] = value
        return out
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(MigrationError("nonfinite-json")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MigrationError("invalid-json:" + str(exc)) from exc

def _exact_keys(obj, keys, label):
    if type(obj) is not dict or set(obj) != set(keys):
        raise MigrationError("invalid-" + label + "-keys")

def _hex(value, label):
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise MigrationError("invalid-" + label)

def _absolute(value, label, *, exists=True, directory=None):
    """Accept only a canonical absolute spelling whose existing components are not aliases."""
    if type(value) is not str or not value or not os.path.isabs(value) or os.path.normpath(value) != value:
        raise MigrationError(label + "-must-be-canonical-absolute")
    path = Path(value)
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            st = current.lstat()
        except FileNotFoundError:
            if exists:
                raise MigrationError("missing-" + label)
            continue
        if stat.S_ISLNK(st.st_mode):
            raise MigrationError("aliased-" + label)
        if current != path and not stat.S_ISDIR(st.st_mode):
            raise MigrationError("unsafe-" + label + "-component")
    if exists:
        st = path.lstat()
        if directory is True and not stat.S_ISDIR(st.st_mode):
            raise MigrationError(label + "-must-be-directory")
        if directory is False and not stat.S_ISREG(st.st_mode):
            raise MigrationError(label + "-must-be-regular-file")
    return path

def _validate_catalog(catalog):
    _exact_keys(catalog, TOP_KEYS, "catalog")
    if catalog["schema"] != CATALOG_SCHEMA or catalog["revision"] != 1 or catalog["target_methodology"] != "10.2.0":
        raise MigrationError("unsupported-catalog")
    if catalog["supported_buckets"] != ["pre-3", "3", "4", "5", "lite"]:
        raise MigrationError("unsupported-catalog-buckets")
    if type(catalog["rules"]) is not list or [r.get("id") for r in catalog["rules"] if type(r) is dict] != list(FAMILIES):
        raise MigrationError("catalog-rule-order")
    for i, rule in enumerate(catalog["rules"]):
        _exact_keys(rule, RULE_KEYS, "rule")
        family = FAMILIES[i]
        if rule["id"] != family or rule["detector"] != family or rule["effect"] != family or rule["postcondition"] != family:
            raise MigrationError("catalog-family-binding:" + family)
        if rule["kind"] != ("optional" if family in {"J", "W", "O"} else "required") or rule["applies"] != APPLIES[family]:
            raise MigrationError("catalog-kind-or-applicability:" + family)
        if rule["requires"] != ([] if i == 0 else [FAMILIES[i - 1]]):
            raise MigrationError("catalog-order-edge:" + family)
        if rule["recovery"] not in {"preserve-original", "reconcile-job", "restore-checkpoint", "defer"}:
            raise MigrationError("catalog-recovery:" + family)
        if type(rule["instructions"]) is not list or not rule["instructions"]:
            raise MigrationError("catalog-instructions:" + family)
        refs = []
        for inst in rule["instructions"]:
            _exact_keys(inst, {"text", "sources"}, "instruction")
            if type(inst["text"]) is not str or not inst["text"].strip() or type(inst["sources"]) is not list:
                raise MigrationError("catalog-instruction-value:" + family)
            if any(type(s) is not str for s in inst["sources"]):
                raise MigrationError("catalog-instruction-source:" + family)
            for source in inst["sources"]:
                try:
                    ident = json.loads(source)
                except (TypeError, json.JSONDecodeError) as exc:
                    raise MigrationError("catalog-instruction-source:" + family) from exc
                if type(ident) is not list or len(ident) != 3 or ident[0] not in {"G", "H"} or type(ident[1]) is not str or type(ident[2]) is not int or ident[2] < 1 or json.dumps(ident, ensure_ascii=False, separators=(",", ":")) != source:
                    raise MigrationError("catalog-instruction-source:" + family)
                refs.append(source)
        if refs != rule["provenance_ids"] or len(refs) != len(set(refs)):
            raise MigrationError("catalog-provenance-coverage:" + family)
        if type(rule["exceptions"]) is not list or any(type(x) is not str for x in rule["exceptions"]):
            raise MigrationError("catalog-exceptions:" + family)
    prov = catalog["provenance"]
    _exact_keys(prov, {"groups", "items"}, "provenance")
    if type(prov["groups"]) is not list or len(prov["groups"]) != 44 or type(prov["items"]) is not list or len(prov["items"]) != 220:
        raise MigrationError("catalog-provenance-count")
    ids_by_family = {family: [] for family in FAMILIES}
    item_counts = {family: 0 for family in FAMILIES}
    seen_items = set()
    for item in prov["items"]:
        _exact_keys(item, {"source", "heading", "index", "sha256", "family"}, "provenance-item")
        if item["source"] not in {"G", "H"} or item["family"] not in FAMILIES or type(item["index"]) is not int or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise MigrationError("catalog-provenance-item")
        ref = json.dumps([item["source"], item["heading"], item["index"]], ensure_ascii=False, separators=(",", ":"))
        if ref in seen_items or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise MigrationError("catalog-provenance-item")
        seen_items.add(ref)
        item_counts[item["family"]] += 1
        ids_by_family[item["family"]].append(ref)
    declared = [r for rule in catalog["rules"] for r in rule["provenance_ids"]]
    if [ref for family in FAMILIES for ref in ids_by_family[family]] != declared:
        raise MigrationError("catalog-provenance-bijection")
    for group in prov["groups"]:
        _exact_keys(group, {"source", "heading", "start", "end", "sha256", "families"}, "provenance-group")
        if group["source"] not in {"G", "H"} or type(group["start"]) is not int or type(group["end"]) is not int or group["start"] < 1 or group["end"] < group["start"] or type(group["families"]) is not list or any(x not in FAMILIES for x in group["families"]) or not re.fullmatch(r"[0-9a-f]{64}", group["sha256"]):
            raise MigrationError("catalog-provenance-group")
    if item_counts != FAMILY_COUNTS:
        raise MigrationError("catalog-family-coverage")
    return catalog

def _tree(root, *, allow_root_missing=False):
    root = Path(root)
    if not root.exists():
        if allow_root_missing:
            return {}
        raise MigrationError("missing-workspace")
    if root.is_symlink() or not root.is_dir():
        raise MigrationError("unsafe-workspace-root")
    files = {}
    for base, dirs, names in os.walk(root, topdown=True, followlinks=False):
        b = Path(base)
        dirs.sort()
        names.sort()
        for name in list(dirs):
            p = b / name
            if p.is_symlink() or not p.is_dir():
                raise MigrationError("unsafe-path:" + str(p))
        for name in names:
            p = b / name
            if p.is_symlink() or not p.is_file():
                raise MigrationError("unsafe-path:" + str(p))
            rel = p.relative_to(root).as_posix()
            files[rel] = p.read_bytes()
    return files

def _inventory(root):
    root = Path(root)
    entries = {}
    if root.is_symlink() or not root.is_dir():
        raise MigrationError("unsafe-inventory-root")
    for base, dirs, names in os.walk(root, topdown=True, followlinks=False):
        b = Path(base)
        for name in sorted(dirs):
            p = b / name
            st = p.lstat()
            if not stat.S_ISDIR(st.st_mode):
                raise MigrationError("unsafe-inventory-path")
            rel = p.relative_to(root).as_posix()
            entries[rel] = {"type": "directory", "mode": stat.S_IMODE(st.st_mode), "sha256": None}
        for name in sorted(names):
            p = b / name
            st = p.lstat()
            if not stat.S_ISREG(st.st_mode):
                raise MigrationError("unsafe-inventory-path")
            rel = p.relative_to(root).as_posix()
            entries[rel] = {"type": "file", "mode": stat.S_IMODE(st.st_mode), "sha256": _sha(p.read_bytes())}
    return entries

def _inventory_sha(entries):
    return _sha(_canonical(entries))

def _validate_inventory(entries, label):
    if type(entries) is not dict:
        raise MigrationError("invalid-" + label + "-inventory")
    for rel, meta in entries.items():
        if type(rel) is not str or not rel or "\\" in rel or PurePosixPath(rel).is_absolute() or PurePosixPath(rel).as_posix() != rel or any(p in {"", ".", ".."} for p in rel.split("/")):
            raise MigrationError("invalid-" + label + "-inventory-path")
        _exact_keys(meta, {"type", "mode", "sha256"}, label + "-inventory-entry")
        if meta["type"] not in {"file", "directory"} or type(meta["mode"]) is not int or not 0 <= meta["mode"] <= 0o7777:
            raise MigrationError("invalid-" + label + "-inventory-entry")
        if meta["type"] == "file": _hex(meta["sha256"], label + "-inventory-hash")
        elif meta["sha256"] is not None: raise MigrationError("invalid-" + label + "-directory-hash")
    return entries

def _source_digest(files):
    return _sha(_canonical({p: _sha(v) for p, v in sorted(files.items())}))

def _methodology(files):
    data = schema.root_files(files).get("AGENTS.md")
    if data is None:
        return None
    text = schema.decode(data)
    m = schema.METHODOLOGY_RE.search(text)
    return m.group(2) if m else None

def _supported_methodology(files, target):
    """Keep observed structure independent; never rewrite a known future stamp."""
    observed = _methodology(files)
    if observed is None: return None
    match = re.fullmatch(r"Tackle (0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:\.(0|[1-9][0-9]*))?(?: candidate)?", observed)
    if match is not None:
        version = tuple(int(value or 0) for value in match.groups())
        target_version = tuple(int(value) for value in target.split("."))
        if version > target_version: raise MigrationError("unsupported-newer-source-methodology:" + observed)
    return observed

def _lite_state(files):
    plan = schema.root_files(files).get("plan.md")
    if plan is None or schema.schema_of(files) != "lite": return None
    lines = [line for line in schema.unfenced_lines(schema.decode(plan), strict=True)
             if not line.lstrip().startswith(">")]
    values = [match[1].strip() for line in lines
              if (match := re.fullmatch(r"- State:\s*(.*?)\s*", line))]
    if len(values) != 1 or any(token in values[0] for token in ("{{", "}}")): return None
    if re.fullmatch(r"(?:Ready|running|blocked|complete)(?:[ \t]+/[ \t]+(?:Ready|running|blocked|complete))+(?:[ \t]+and next action)?", values[0]): return None
    match = re.fullmatch(r"(Ready|running|blocked|complete)(?:[ \t]+.+)?", values[0])
    return match[1] if match else None

def _board_observation(files):
    roots = schema.root_files(files)
    board_name = "task-board.md" if "task-board.md" in roots else "board.md" if "board.md" in roots else None
    if not board_name:
        return None, "unknown", []
    try:
        _, _, header, rows = schema.parse_board(schema.decode(roots[board_name]))
        sc = schema.column_index(header, "Status")
        ic = schema.column_index(header, "Task")
        if ic is None: ic = schema.column_index(header, "Point")
        if sc is None or ic is None:
            return board_name, "unknown", []
        states = []
        seen = set()
        valid = True
        for _, cells in rows:
            task = cells[ic].strip() if ic is not None and ic < len(cells) else ""
            status = cells[sc].strip() if sc < len(cells) else ""
            if status in schema.LEGACY_STATE_MAP: status = schema.LEGACY_STATE_MAP[status]
            if task:
                if not re.fullmatch(schema.ID_RE, task):
                    continue
                if task in seen: valid = False
                seen.add(task)
            if status not in schema.VALID_STATES: valid = False
            states.append((task, status))
        return board_name, "observed" if valid else "unknown", states
    except (ValueError, UnicodeError, IndexError):
        return board_name, "unknown", []

def _validate_context(context):
    _exact_keys(context, CONTEXT_KEYS, "context")
    if type(context["workspace"]) is not str or not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", context["workspace"]):
        raise MigrationError("invalid-workspace-name")
    if context["target"] != "10.2.0":
        raise MigrationError("unsupported-target")
    if type(context["date"]) is not str or not re.fullmatch(r"\d{4}-\d\d-\d\d", context["date"]):
        raise MigrationError("invalid-date")
    try:
        time.strptime(context["date"], "%Y-%m-%d")
    except ValueError as exc:
        raise MigrationError("invalid-date") from exc
    if type(context["run_id"]) is not str or not context["run_id"].strip():
        raise MigrationError("invalid-run-id")
    for key in ("next_wave", "optional_requests"):
        value = context[key]
        if type(value) is not list or any(type(x) is not str or not x.strip() for x in value) or len(value) != len(set(value)):
            raise MigrationError("invalid-" + key)
    if any(x not in {"J", "W", "O"} for x in context["optional_requests"]):
        raise MigrationError("invalid-optional-request")
    if any(not re.fullmatch(r"T-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", x) for x in context["next_wave"]):
        raise MigrationError("invalid-next-wave-id")
    boundary = context["boundary"]
    _exact_keys(boundary, {"at_boundary", "source_receipt_sha256"}, "boundary")
    if type(boundary["at_boundary"]) is not bool or type(boundary["source_receipt_sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", boundary["source_receipt_sha256"]):
        raise MigrationError("invalid-boundary")
    return context

def _declared_briefs(files):
    board, quality, _ = _board_observation(files)
    if board is None or quality != "observed": return {}
    _, _, header, rows = schema.parse_board(schema.decode(files[board]))
    task_col = schema.column_index(header, "Task")
    if task_col is None: task_col = schema.column_index(header, "Point")
    brief_col = schema.column_index(header, "Brief")
    if task_col is None or brief_col is None: return {}
    bindings = {}
    for _, cells in rows:
        task = cells[task_col].strip()
        if not re.fullmatch(schema.ID_RE, task): continue
        raw = cells[brief_col].strip().strip("`")
        if not raw or raw in {"—", "-", "n/a"}: continue
        path = PurePosixPath(raw)
        if (path.is_absolute() or path.as_posix() != raw or "\\" in raw
                or any(part in {"", ".", ".."} for part in raw.split("/"))
                or not raw.startswith(("tasks/", "points/") if schema.schema_of(files) in {"pre-3", "3", "4"} else ("tasks/",))
                or path.suffix != ".md"):
            raise MigrationError("unsafe-declared-brief:" + task)
        if task in bindings and bindings[task] != raw:
            raise MigrationError("ambiguous-declared-brief:" + task)
        bindings[task] = raw
    return bindings

def _brief_path(files, task, bindings, *, required=True):
    if task in bindings:
        path = bindings[task]
        if path not in files:
            if required: raise MigrationError("declared-brief-missing:" + task)
            return None
        return path
    # Retained layouts are fallback alternatives, only when exactly one exists.
    names = {"tasks/" + task + ".md", "tasks/" + task + "-brief.md", "tasks/" + task + "/brief.md"}
    names.update(path for path in files if path.startswith("tasks/" + task + "-")
                 and path.endswith(".md") and "/" not in path[len("tasks/"):])
    found = sorted(names.intersection(files))
    if len(found) != 1:
        if required or found: raise MigrationError("next-wave-brief-missing-or-ambiguous:" + task)
        return None
    return found[0]

def _current_fields(data):
    lines = [line for line in schema.unfenced_lines(schema.decode(data), strict=True)
             if not line.lstrip().startswith(">")]
    fields = task_fields("\n".join(lines))
    for line in lines:
        match = re.fullmatch(r"\s*(?:-\s*)?(Repository|Requires|Requirements base):\s*(.*?)\s*", line)
        if match:
            if match[1] in fields and fields[match[1]] != match[2]:
                raise MigrationError("conflicting-current-field:" + match[1])
            fields[match[1]] = match[2]
    return fields

def diagnose(files, context, catalog):
    """Pure diagnosis over supplied path->bytes, context, and validated catalog."""
    _validate_catalog(catalog)
    _validate_context(context)
    if type(files) is not dict or any(type(p) is not str or type(b) is not bytes for p, b in files.items()):
        raise MigrationError("invalid-file-map")
    for p in files:
        q = PurePosixPath(p)
        if q.is_absolute() or not p or q.as_posix() != p or any(part in {"", ".", ".."} for part in p.split("/")) or "\\" in p:
            raise MigrationError("unsafe-relative-path")
    roots = schema.root_files(files)
    if "board.md" in roots and "task-board.md" in roots:
        raise MigrationError("conflicting-root-board-carriers")
    for board_name in ("board.md", "task-board.md"):
        if board_name in roots:
            schema.unfenced_lines(schema.decode(roots[board_name]), strict=True)
    bucket = schema.schema_of(files)
    methodology = _supported_methodology(files, catalog["target_methodology"])
    board_name, board_quality, rows = _board_observation(files)
    state_by_id = {task: state for task, state in rows if task}
    if board_quality == "observed":
        for task in context["next_wave"]:
            if task not in state_by_id:
                raise MigrationError("next-wave-task-not-on-observed-board:" + task)
            if state_by_id[task] not in {"Draft", "Ready to run"}:
                raise MigrationError("next-wave-task-not-unstarted:" + task)
    requested = set(context["optional_requests"])
    selected_states = {"Draft", "Ready to run"}
    interrupted_states = {"Interrupted", "Checking"}
    started_states = {"In progress", "Blocked"}
    active = any(state in selected_states | interrupted_states | started_states for state in state_by_id.values())
    lite_state = _lite_state(files) if bucket == "lite" else None
    if bucket == "lite" and lite_state in {"Ready", "running", "blocked"}:
        if context["next_wave"]: raise MigrationError("lite-next-wave-has-no-full-board")
        classification = "selected-active" if lite_state == "Ready" else "started"
    elif board_quality != "observed" or bucket == "unknown":
        classification = "unknown"
    elif any(state in interrupted_states for state in state_by_id.values()):
        classification = "interrupted"
    elif any(state in started_states for state in state_by_id.values()):
        classification = "started"
    elif any(state in selected_states for state in state_by_id.values()):
        classification = "selected-active"
    else:
        # Complete/Skipped remain board states; accepted closure needs separate
        # delivery/obligation evidence and is never inferred here.
        classification = "unknown"
    bindings = _declared_briefs(files)
    for task in context["next_wave"]:
        _brief_path(files, task, bindings)
    repository_fields = set()
    current_requirement_consumer = False
    for task, status in rows:
        if not task or status in {"Complete", "Skipped", "Unverifiable"}: continue
        path = _brief_path(files, task, bindings, required=task in context["next_wave"])
        if path is None: continue
        # Historical field names are observations for the structural adapter,
        # not a current target brief passed to the current readiness consumer.
        lines = [line for line in schema.unfenced_lines(schema.decode(files[path]), strict=True)
                 if not line.lstrip().startswith(">")]
        selected = [line for line in lines if re.match(r"^\s*(?:-\s*)?\*\*(?:Repository|Requires|Requirements base)(?:\*\*\s*:|:\*\*)", line)]
        fields = task_fields("\n".join(selected))
        for line in lines:
            match = re.fullmatch(r"\s*(?:-\s*)?(Repository|Requires|Requirements base):\s*(.*?)\s*", line)
            if match:
                if match[1] in fields and fields[match[1]] != match[2]: raise MigrationError("conflicting-current-field:" + match[1])
                fields[match[1]] = match[2]
        repository = fields.get("Repository", "").strip().strip("`")
        if repository and repository not in {"none", "n/a", "—"}: repository_fields.add(repository)
        for key in ("Requires", "Requirements base"):
            if re.search(r"(?:^|[/`\s])requirements-base(?:\.md)?(?:#|\b)", fields.get(key, "")):
                current_requirement_consumer = True
    provenance_by_family = {f: [] for f in FAMILIES}
    for item in catalog["provenance"]["items"]:
        ref = json.dumps([item["source"], item["heading"], item["index"]], ensure_ascii=False, separators=(",", ":"))
        provenance_by_family[item["family"]].append((ref, item))
    obligations, actions, manual, write_paths = [], [], [], []
    active_classifications = {"selected-active", "started", "interrupted"}
    family_apply = {"I": True, "P": classification in active_classifications, "S": bucket in {"pre-3", "3", "4", "lite"}, "A": bucket in {"pre-3", "3", "4", "lite"}, "R": classification in active_classifications, "B": bool(context["next_wave"]), "M": classification in active_classifications, "E": classification in active_classifications, "J": "J" in requested, "H": classification in active_classifications, "N": len(repository_fields) > 1, "Q": current_requirement_consumer, "W": "W" in requested, "O": "O" in requested, "V": classification in active_classifications, "Z": classification in active_classifications or bucket in {"pre-3", "3", "4", "lite"}}
    for rule in catalog["rules"]:
        f = rule["id"]
        applies = family_apply[f]
        if f == "N": applies = len(repository_fields) > 1
        if f == "Q": applies = current_requirement_consumer
        state = "not-applicable" if not applies else "unknown"
        if f == "S" and bucket == "5": state = "satisfied"
        for ref, item in provenance_by_family[f]:
            obligations.append({"id": ref, "family": f, "kind": rule["kind"], "state": state, "sources": [ref], "consumer": "installed compact migration route", "check": f, "evidence": []})
        if applies and state in {"unknown", "pending"}:
            manual.append({"id": f, "family": f, "state": state, "required": rule["kind"] == "required", "reason": "required current evidence or owner decision is not established by source facts"})
    # Only real structural transformations become write effects here. Other families
    # remain obligations/manual facts until their independent evidence is supplied.
    preview = dict(files)
    before_paths = dict(files)
    if bucket in {"pre-3", "3", "4", "lite"}:
        try:
            preview = _adapter_chain(files, methodology, context)
        except (MigrationError, ValueError, KeyError, TypeError) as exc:
            family_apply["S"] = True
            for row in obligations:
                if row["family"] == "S": row["state"] = "unknown"
            manual.append({"id": "S", "family": "S", "state": "unknown", "required": True, "reason": "structural adapter refused: " + str(exc)})
            preview = dict(files)
    changed = sorted(path for path in set(before_paths) | set(preview) if before_paths.get(path) != preview.get(path))
    if changed:
        effect_tuple = ("structural-adapter", tuple(changed), ("source inventory pinned", "exact adapter detected", "schema.verify passed"), None, "schema.adopt", ("target schema verified", "legacy snapshots preserved"))
        actions.append({"family": "S", "effect": effect_tuple[0], "paths": list(effect_tuple[1]), "preconditions": list(effect_tuple[2]), "consent_source": effect_tuple[3], "consumer": effect_tuple[4], "postconditions": list(effect_tuple[5])})
        write_paths.extend(changed)
    obligations.sort(key=lambda row: (FAMILIES.index(row["family"]), row["id"]))
    if family_apply["Z"]:
        paths = [name for name in ("history.md", "AGENTS.md") if name in preview]
        if paths:
            actions.append({"family": "Z", "effect": "candidate-marker-and-stamp", "paths": paths,
                            "preconditions": ["existing history carrier", "pre-stamp captures retained", "dated history order valid"],
                            "consent_source": None, "consumer": "installed candidate transition and post-stamp lint",
                            "postconditions": ["exact candidate event appended once", "methodology stamp follows event", "distinct post-stamp capture binds frozen candidate"]})
            write_paths.extend(paths)
    catalog_raw = _canonical(catalog)
    file_map_sha = _source_digest(files)
    plan = {"schema": PLAN_SCHEMA, "context": context, "target": context["target"], "catalog_sha256": _sha(catalog_raw), "tool_sha256": None, "install_sha256": None, "source": {"workspace": context["workspace"], "path": None, "files_sha256": file_map_sha, "inventory": None, "sha256": None}, "observed": {"bucket": bucket, "methodology": methodology, "classification": classification}, "obligations": obligations, "actions": actions, "manual": manual, "write_paths": sorted(set(write_paths)), "preserved_paths": sorted(files), "metrics": {"planned_legacy_actions": sum(row["state"] != "not-applicable" for row in obligations), "planned_selected_actions": None, "planned_actions_avoided": None, "files_read": len(files), "structural_transforms": 1 if changed else 0, "view_rebuilds": 0, "checks_executed": 0, "wall_ms": None}, "operation_id": None}
    plan["operation_id"] = _sha(_canonical({k: v for k, v in plan.items() if k != "operation_id"}))
    return plan

def _atomic(path, data, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink(): raise MigrationError("unsafe-record-path")
    if path.exists() and path.read_bytes() == data:
        return
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
        dfd = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(dfd)
        finally: os.close(dfd)
    except Exception:
        with contextlib.suppress(OSError): os.unlink(tmp)
        raise

def _write_state(job, state):
    _atomic(Path(job) / "state.json", _canonical(state))

def _load_state_data(job):
    job = _absolute(str(job), "job", exists=True, directory=True)
    state = _read_json(job / "state.json")
    _exact_keys(state, {"schema", "operation_id", "operation", "phase", "source", "checkpoint", "candidate", "original_backup", "adopted_backup", "restore_stage", "source_sha256", "candidate_sha256", "checkpoint_sha256", "install_sha256", "catalog_sha256", "context_sha256", "boundary_sha256", "receipts"}, "job-state")
    if state["schema"] != JOB_SCHEMA:
        raise MigrationError("invalid-job-state")
    if type(state["operation_id"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", state["operation_id"]):
        raise MigrationError("invalid-job-operation")
    if state["operation"] not in {"adopt", "restore"} or state["phase"] not in {"prepared", "verified", "adopt-intent", "original-backed-up", "candidate-promoted", "adopted", "restore-intent", "adopted-backed-up", "restored"}:
        raise MigrationError("invalid-job-phase")
    for key in ("source", "checkpoint", "candidate", "original_backup", "adopted_backup", "restore_stage"):
        _absolute(state[key], "job-path", exists=key == "checkpoint", directory=True)
    expected = {"checkpoint": job / "checkpoint", "candidate": job / "candidate-project" / "docs" / "plans" / Path(state["source"]).name,
                "original_backup": job / "original-backup", "adopted_backup": job / "adopted-backup", "restore_stage": job / "restore-stage"}
    for key, path in expected.items():
        if Path(state[key]) != path:
            raise MigrationError("invalid-designated-job-path:" + key)
    if Path(state["source"]).is_relative_to(job):
        raise MigrationError("source-inside-job")
    for key in ("source_sha256", "candidate_sha256", "checkpoint_sha256", "install_sha256", "catalog_sha256", "context_sha256", "boundary_sha256"):
        _hex(state[key], "state-" + key)
    if type(state["receipts"]) is not list:
        raise MigrationError("invalid-state-receipts")
    for ref in state["receipts"]:
        _exact_keys(ref, {"path", "sha256"}, "receipt-ref")
        if type(ref["path"]) is not str or not ref["path"] or Path(ref["path"]).is_absolute():
            raise MigrationError("invalid-receipt-path")
        _hex(ref["sha256"], "receipt-hash")
    return state

def _load_state(job):
    try:
        return _load_state_data(job)
    except (MigrationError, OSError, ValueError, KeyError, TypeError) as exc:
        raise PendingError("existing-job-state-conflict:" + str(exc)) from exc

@contextlib.contextmanager
def _parent_lock(source):
    source = Path(source)
    parent = source.parent.resolve(strict=True)
    name = ".tackle-migrate-" + source.name + ".lock"
    path = parent / name
    if path.is_symlink() or (path.exists() and not stat.S_ISREG(path.lstat().st_mode)):
        raise MigrationError("unsafe-parent-lock")
    fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        os.close(fd)
        raise PendingError("migration-busy") from exc
    try: yield fd
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN); os.close(fd)

def _materialize(files, root, inventory=None):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    inventory = inventory or {}
    for rel, meta in sorted(inventory.items()):
        if meta.get("type") == "directory":
            p = root.joinpath(*PurePosixPath(rel).parts)
            p.mkdir(parents=True, exist_ok=True)
    for rel, data in sorted(files.items()):
        p = root.joinpath(*PurePosixPath(rel).parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            mode = inventory.get(rel, {}).get("mode", 0o644)
            os.chmod(p, mode)
        except BaseException:
            with contextlib.suppress(OSError): p.unlink()
            raise
    for rel, meta in sorted(inventory.items(), key=lambda item: item[0].count("/"), reverse=True):
        if meta.get("type") == "directory":
            os.chmod(root.joinpath(*PurePosixPath(rel).parts), meta["mode"])
    _fsync_dir(root)

def _copy_bytes(source, dest):
    files = _tree(source)
    inventory = _inventory(source)
    _materialize(files, dest, inventory)
    if _inventory_sha(_inventory(dest)) != _inventory_sha(inventory):
        raise MigrationError("copy-inventory-mismatch")
    return files

def _project_directories(directories, files, bucket, id_map=None):
    """Mirror this actual adoption's path map and legacy snapshot for directory metadata."""
    prefix = "legacy-" + bucket
    if prefix in directories:
        raise MigrationError("snapshot-directory-collision:" + prefix)
    projected = {}

    def claim(path, meta):
        if path in files:
            raise MigrationError("directory-file-collision:" + path)
        if path in projected:
            raise MigrationError("directory-target-collision:" + path)
        projected[path] = dict(meta)

    for path, meta in directories.items():
        if schema.is_legacy_path(path):
            claim(path, meta)
    claim(prefix, {"type": "directory", "mode": 0o755, "sha256": None})
    for path, meta in directories.items():
        if schema.is_legacy_path(path):
            continue
        target = step_3_to_4._path_target(path, id_map).rstrip("/") if bucket == "3" else path
        claim(target, meta)
        claim(prefix + "/" + path, meta)
    return projected

def _transformed_inventory(before, after, original_inventory, directories):
    old_by_hash = {}
    for path, meta in original_inventory.items():
        if meta["type"] == "file": old_by_hash.setdefault(meta["sha256"], []).append(meta["mode"])
    result = {}
    for path, meta in directories.items():
        result[path] = dict(meta)
    for path, data in after.items():
        if path in result:
            raise MigrationError("directory-file-collision:" + path)
        if path in original_inventory and original_inventory[path]["type"] == "file" and before.get(path) == data:
            mode = original_inventory[path]["mode"]
        elif path.startswith("legacy-") and "/" in path:
            old = path.split("/", 1)[1]
            mode = original_inventory.get(old, {}).get("mode", 0o644)
        else:
            matches = old_by_hash.get(_sha(data), [])
            mode = matches[0] if len(set(matches)) == 1 and matches else 0o644
        result[path] = {"type": "file", "mode": mode, "sha256": _sha(data)}
        parts = PurePosixPath(path).parts[:-1]
        for index in range(1, len(parts) + 1):
            directory = PurePosixPath(*parts[:index]).as_posix()
            result.setdefault(directory, {"type": "directory", "mode": original_inventory.get(directory, {}).get("mode", 0o755), "sha256": None})
    return result

def _fsync_dir(path):
    fd = os.open(Path(path), os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

_HELD_CONTEXT_LOCKS = set()

@contextlib.contextmanager
def _context_lock(path, *, required=False):
    """Hold an existing Context inode; absence never creates source authority."""
    lock = Path(path) / ".context-lock"
    try: observed = lock.lstat()
    except FileNotFoundError:
        if required: raise PendingError("context-writer-lock-unavailable")
        yield
        return
    if not stat.S_ISREG(observed.st_mode): raise PendingError("unsafe-context-lock")
    identity = (observed.st_dev, observed.st_ino)
    # Internal nested helpers share the descriptor already held by this process.
    if identity in _HELD_CONTEXT_LOCKS:
        yield
        return
    fd = os.open(lock, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        actual = os.fstat(fd)
        if (actual.st_dev, actual.st_ino) != identity or not stat.S_ISREG(actual.st_mode):
            raise PendingError("context-lock-replaced")
        try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc: raise PendingError("migration-busy") from exc
        _HELD_CONTEXT_LOCKS.add(identity)
        try:
            yield
            current = lock.lstat() if lock.exists() else None
            # A cutover can move this inode to its designated backup, so the
            # carrier check is made before every effect, not at release.
            if current is not None and not stat.S_ISREG(current.st_mode):
                raise PendingError("context-lock-carrier-changed")
        finally: _HELD_CONTEXT_LOCKS.remove(identity)
    finally:
        with contextlib.suppress(OSError): fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

@contextlib.contextmanager
def _existing_context_locks(*paths):
    """Retain every existing carrier lock in the declared source/stage order."""
    with contextlib.ExitStack() as stack:
        seen = set()
        for path in paths:
            carrier = Path(path)
            if carrier in seen: continue
            seen.add(carrier)
            if carrier.is_symlink(): raise PendingError("aliased-lock-carrier")
            if carrier.exists(): stack.enter_context(_context_lock(carrier))
        yield

def _adapter_chain(files, source_methodology, context, *, directories=None):
    result = dict(files)
    directory_state = None if directories is None else {path: dict(meta) for path, meta in directories.items()}
    bucket = schema.schema_of(result)
    ctx = {"methodology": source_methodology, "date": context["date"],
           "run_id": context["run_id"], "workspace": context["workspace"]}
    if bucket == "pre-3":
        if not step_pre3_to_3.detect(result): raise MigrationError("pre3-detection-conflict")
        next_files, _ = schema.adopt(result, ctx, step_pre3_to_3.transform)
        checked = step_pre3_to_3.verify(schema.workspace_files(result), schema.workspace_files(next_files))
        if checked.get("errors"): raise MigrationError("pre3-verify:" + ";".join(checked["errors"]))
        if directory_state is not None:
            directory_state = _project_directories(directory_state, next_files, "pre-3")
        result = next_files; bucket = schema.schema_of(result)
    if bucket == "3":
        if not step_3_to_4.detect(result): raise MigrationError("schema3-detection-conflict")
        next_files, id_map = schema.adopt(result, ctx, step_3_to_4.transform)
        checked = step_3_to_4.verify(schema.workspace_files(result), schema.workspace_files(next_files))
        if checked.get("errors"): raise MigrationError("schema3-verify:" + ";".join(checked["errors"]))
        if directory_state is not None:
            directory_state = _project_directories(directory_state, next_files, "3", id_map)
        result = next_files; bucket = schema.schema_of(result)
    if bucket == "4":
        if not step_4_to_5.detect(result): raise MigrationError("schema4-detection-conflict")
        next_files, _ = schema.adopt(result, ctx, step_4_to_5.transform)
        checked = step_4_to_5.verify(schema.workspace_files(result), schema.workspace_files(next_files))
        if checked.get("errors"): raise MigrationError("schema4-verify:" + ";".join(checked["errors"]))
        if directory_state is not None:
            directory_state = _project_directories(directory_state, next_files, "4")
        result = next_files; bucket = schema.schema_of(result)
    if bucket == "lite":
        for old, new in (("log.md", "history.md"), ("log-archive.md", "history-archive.md"), ("usage.md", "resource-usage.md")):
            if old in result:
                if new in result: raise MigrationError("lite-path-collision:" + new)
                result[new] = result.pop(old)
    if bucket not in {"5", "lite"}:
        raise MigrationError("unsupported-source-bucket:" + bucket)
    if directories is not None:
        directories.clear(); directories.update(directory_state)
    return result

def _manifest(path, *, allow_source_missing=False):
    m = _read_json(_absolute(str(path), "manifest", exists=True, directory=False))
    plan_keys = {"schema", "context", "target", "catalog_sha256", "tool_sha256", "install_sha256", "source", "observed", "obligations", "actions", "manual", "write_paths", "preserved_paths", "metrics", "operation_id"}
    _exact_keys(m, plan_keys, "manifest")
    if m["schema"] != PLAN_SCHEMA or type(m["operation_id"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", m["operation_id"]):
        raise MigrationError("invalid-manifest")
    if m["operation_id"] != _sha(_canonical({k: v for k, v in m.items() if k != "operation_id"})):
        raise MigrationError("manifest-operation-id-mismatch")
    _validate_context(m["context"])
    _hex(m["catalog_sha256"], "catalog-hash"); _hex(m["tool_sha256"], "tool-hash"); _hex(m["install_sha256"], "install-hash")
    _exact_keys(m["source"], {"workspace", "path", "files_sha256", "inventory", "sha256"}, "manifest-source")
    if type(m["source"]["workspace"]) is not str or m["source"]["workspace"] != m["context"]["workspace"]:
        raise MigrationError("source-context-mismatch")
    _absolute(m["source"]["path"], "source", exists=not allow_source_missing, directory=True)
    if Path(m["source"]["path"]).name != m["context"]["workspace"]:
        raise MigrationError("source-context-mismatch")
    _hex(m["source"]["files_sha256"], "file-map-hash"); _hex(m["source"]["sha256"], "source-inventory-hash")
    inventory = _validate_inventory(m["source"]["inventory"], "source")
    if _inventory_sha(inventory) != m["source"]["sha256"]:
        raise MigrationError("manifest-source-inventory-hash-mismatch")
    _exact_keys(m["observed"], {"bucket", "methodology", "classification"}, "observed")
    if m["observed"]["bucket"] not in {"pre-3", "3", "4", "5", "lite", "unknown"} or m["observed"]["classification"] not in {"selected-active", "started", "interrupted", "accepted-closed", "unknown"} or (m["observed"]["methodology"] is not None and type(m["observed"]["methodology"]) is not str):
        raise MigrationError("invalid-observed-facts")
    for row in m["obligations"]:
        _exact_keys(row, {"id", "family", "kind", "state", "sources", "consumer", "check", "evidence"}, "obligation")
        if row["family"] not in FAMILIES or row["kind"] not in {"required", "optional"} or row["state"] not in {"satisfied", "pending", "not-applicable", "unknown"} or type(row["id"]) is not str or type(row["sources"]) is not list or type(row["evidence"]) is not list:
            raise MigrationError("invalid-obligation")
        if type(row["consumer"]) is not str or type(row["check"]) is not str or any(type(ref) is not str for ref in row["sources"]):
            raise MigrationError("invalid-obligation-values")
    for row in m["actions"]:
        _exact_keys(row, {"family", "effect", "paths", "preconditions", "consent_source", "consumer", "postconditions"}, "action")
        if row["family"] not in FAMILIES or type(row["effect"]) is not str or type(row["paths"]) is not list or type(row["preconditions"]) is not list or type(row["postconditions"]) is not list:
            raise MigrationError("invalid-action")
    return m

def _cmd_diagnose(args):
    root = _absolute(args.workspace, "workspace", exists=True, directory=True)
    if args.target != "10.2.0": raise MigrationError("unsupported-target")
    context = _read_json(_absolute(args.context, "context", exists=True, directory=False))
    catalog_path = Path(__file__).resolve().parents[2] / "references" / "guides" / CATALOG_NAME
    catalog = _validate_catalog(_read_json(catalog_path))
    files = _tree(root)
    if context.get("workspace") != root.name: raise MigrationError("workspace-context-mismatch")
    plan = diagnose(files, context, catalog)
    entries = _inventory(root)
    plan["source"]["path"] = str(root)
    plan["source"]["inventory"] = entries
    plan["source"]["sha256"] = _inventory_sha(entries)
    plan["tool_sha256"] = _sha(Path(__file__).read_bytes())
    plan["install_sha256"] = _install_identity(Path(__file__).resolve().parents[2])
    plan["operation_id"] = _sha(_canonical({k: v for k, v in plan.items() if k != "operation_id"}))
    output = _absolute(args.output, "output", exists=False)
    if output.exists() or output.is_symlink(): raise MigrationError("output-must-be-new-absolute")
    _absolute(str(output.parent), "output-parent", exists=True, directory=True)
    if output.is_relative_to(root):
        raise MigrationError("output-must-be-external")
    _atomic(output, _canonical(plan))
    return 0

def _install_identity(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir(): raise MigrationError("invalid-install-root")
    required = ("SKILL.md", "scripts/migrate/compact.py", "scripts/migrate/schema.py",
                "scripts/migrate/step_pre3_to_3.py", "scripts/migrate/step_3_to_4.py", "scripts/migrate/step_4_to_5.py",
                "scripts/context_bundle.py", "scripts/lint_runner.py", "scripts/lint.py", "scripts/decompose_check.py",
                "references/guides/run-card.md", "references/guides/plan-card.md",
                "references/guides/migrate.md", "references/guides/migration-catalog.json")
    for name in required:
        resource = root / name
        if resource.is_symlink() or not resource.is_file():
            raise MigrationError("missing-required-installed-resource:" + name)
    selected = {"SKILL.md": (root / "SKILL.md").read_bytes()}
    for area in ("references", "scripts"):
        base = root / area
        if base.is_symlink() or not base.is_dir(): raise MigrationError("incomplete-install-artifact")
        for path in sorted(base.rglob("*")):
            if path.is_symlink(): raise MigrationError("aliased-install-resource")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                selected[path.relative_to(root).as_posix()] = path.read_bytes()
    return _source_digest(selected)

def _cmd_prepare(args):
    manifest = _manifest(args.manifest, allow_source_missing=True)
    job = _absolute(args.job, "job", exists=False)
    if job.exists():
        st = _load_state(job)
        if st["operation_id"] != manifest["operation_id"]:
            raise PendingError("job-bound-to-different-operation")
        with _parent_lock(st["source"]), _existing_context_locks(st["source"], st["candidate"], st["original_backup"], st["adopted_backup"]):
            saved, _ = _revalidate_authority(job, st)
            if saved != manifest: raise PendingError("existing-job-manifest-conflict")
            if st["phase"] in {"adopted", "restored"}: return _completed(job, st)
            if st["phase"] not in {"prepared", "verified"}: raise PendingError("prepare-interrupted-operation")
            if (_inventory_sha(_inventory(st["source"])) != st["source_sha256"]
                    or _inventory_sha(_inventory(st["candidate"])) != st["candidate_sha256"]):
                raise PendingError("completed-prepare-mismatch")
            return 0
    src = Path(manifest["source"]["path"])
    parent = _absolute(str(job.parent), "job-parent", exists=True, directory=True)
    if src == job or src in job.parents or job in src.parents:
        raise MigrationError("unsafe-job-location")
    if not src.is_dir(): raise PendingError("source-missing-or-drifted")
    if os.stat(src).st_dev != os.stat(parent).st_dev: raise MigrationError("different-filesystem")
    try:
        installed = _install_identity(Path(__file__).resolve().parents[2])
        catalog_path = Path(__file__).resolve().parents[2] / "references/guides" / CATALOG_NAME
        catalog = _validate_catalog(_read_json(catalog_path))
    except (MigrationError, OSError, ValueError, KeyError, TypeError) as exc:
        raise PendingError("prepared-install-resource-drift:" + str(exc)) from exc
    if manifest["tool_sha256"] != _sha(Path(__file__).read_bytes()) or manifest["install_sha256"] != installed:
        raise PendingError("install-drift")
    if _sha(_canonical(catalog)) != manifest["catalog_sha256"]: raise PendingError("catalog-drift")
    _supported_methodology(_tree(src), catalog["target_methodology"])
    with _parent_lock(src), _context_lock(src):
        entries = _inventory(src)
        if _inventory_sha(entries) != manifest["source"]["sha256"] or _source_digest(_tree(src)) != manifest["source"]["files_sha256"]:
            raise PendingError("source-drift")
        _supported_methodology(_tree(src), catalog["target_methodology"])
        job.parent.stat()
        if job.exists() or job.is_symlink(): raise PendingError("job-already-exists")
        job.mkdir(mode=0o700)
        checkpoint = job / "checkpoint"
        original = _tree(src)
        _materialize(original, checkpoint, entries)
        source_project = job / "source-project" / "docs" / "plans" / src.name
        candidate = job / "candidate-project" / "docs" / "plans" / src.name
        source_project.parent.mkdir(parents=True)
        candidate.parent.mkdir(parents=True)
        _materialize(original, source_project, entries)
        directories = {path: dict(meta) for path, meta in entries.items() if meta["type"] == "directory"}
        transformed = _adapter_chain(original, manifest["observed"]["methodology"], manifest["context"], directories=directories)
        transformed_inventory = _transformed_inventory(original, transformed, entries, directories)
        _materialize(transformed, candidate, transformed_inventory)
        # Use the shipped Context writer protocol to establish the candidate lock
        # that later phases will cooperate with; do not invent a lock format.
        with Context(candidate).writer():
            pass
        transformed_inventory = _inventory(candidate)
        source_sha = manifest["source"]["sha256"]
        st = {"schema": JOB_SCHEMA, "operation_id": manifest["operation_id"], "operation": "adopt", "phase": "prepared", "source": str(src), "checkpoint": str(checkpoint), "candidate": str(candidate), "original_backup": str(job / "original-backup"), "adopted_backup": str(job / "adopted-backup"), "restore_stage": str(job / "restore-stage"), "source_sha256": source_sha, "candidate_sha256": _inventory_sha(_inventory(candidate)), "checkpoint_sha256": _inventory_sha(_inventory(checkpoint)), "install_sha256": manifest["install_sha256"], "catalog_sha256": manifest["catalog_sha256"], "context_sha256": _sha(_canonical(manifest["context"])), "boundary_sha256": manifest["context"]["boundary"]["source_receipt_sha256"], "receipts": []}
        _atomic(job / "manifest.json", _canonical(manifest))
        _write_state(job, st)
        return 0

def _ref(job, relative):
    rel = PurePosixPath(relative) if type(relative) is str else PurePosixPath("/")
    path = Path(relative) if type(relative) is str else Path("/")
    if path.is_absolute() or not path.parts or rel.as_posix() != relative or any(part in {"", ".", ".."} for part in rel.parts):
        raise MigrationError("unsafe-job-reference")
    target = Path(job)
    for index, part in enumerate(rel.parts):
        target = target / part
        if target.is_symlink(): raise MigrationError("aliased-job-evidence:" + rel.as_posix())
        if index < len(rel.parts) - 1 and (not target.exists() or not target.is_dir()):
            raise MigrationError("missing-job-evidence:" + rel.as_posix())
    if not target.is_file(): raise MigrationError("missing-job-evidence:" + rel.as_posix())
    return {"path": path.as_posix(), "sha256": _sha(target.read_bytes())}

def _evidence_ref(job, state, reference):
    _exact_keys(reference, {"path", "sha256"}, "evidence-reference")
    _hex(reference["sha256"], "evidence-hash")
    raw = reference["path"]
    if type(raw) is not str or not raw: raise PendingError("invalid-evidence-path")
    if not Path(raw).is_absolute():
        actual = _ref(job, raw)
    else:
        _absolute(raw, "external-evidence", exists=False)
        target = _evidence_path(job, state, raw)
        _absolute(str(target), "external-evidence", exists=True, directory=False)
        actual = {"path": raw, "sha256": _sha(target.read_bytes())}
    if actual != reference: raise PendingError("evidence-hash-mismatch")
    return actual

def _evidence_path(job, state, raw):
    path = Path(raw)
    if not path.is_absolute(): return Path(job) / path
    source = Path(state["source"])
    # The original identity moves at cutover; raw references keep their spelling.
    # Only the recorded original-backup carrier may resolve that old identity.
    backup = Path(state["original_backup"])
    if path.is_relative_to(source) and backup.exists() and state["phase"] in {
            "adopt-intent", "original-backed-up", "candidate-promoted", "adopted",
            "restore-intent", "adopted-backed-up", "restored"}:
        return backup / path.relative_to(source)
    return path

def _external_receipt_context(target, value, job, state):
    if type(value) is not dict or value.get("schema") != "tackle-migration-review/1": return job, state
    _exact_keys(value, {"schema", "reviewer", "candidate_sha256", "source_sha256", "catalog_sha256", "decisions"}, "semantic-review")
    if target.name != "semantic-review.json": raise PendingError("unbound-external-review-owner")
    owner = _absolute(str(target.parent), "external-review-job", exists=True, directory=True)
    if owner == Path(job): return job, state
    owned = _load_state(owner)
    manifest = _manifest(owner / "manifest.json", allow_source_missing=True)
    if (owned["operation_id"] != manifest["operation_id"]
            or owned["source"] != manifest["source"]["path"]
            or owned["source_sha256"] != manifest["source"]["sha256"]
            or owned["checkpoint_sha256"] != owned["source_sha256"]
            or owned["context_sha256"] != _sha(_canonical(manifest["context"]))
            or owned["boundary_sha256"] != manifest["context"]["boundary"]["source_receipt_sha256"]
            or owned["install_sha256"] != manifest["install_sha256"]
            or owned["catalog_sha256"] != manifest["catalog_sha256"]
            or value["candidate_sha256"] != owned["candidate_sha256"]
            or value["source_sha256"] != owned["source_sha256"]
            or value["catalog_sha256"] != owned["catalog_sha256"]):
        raise PendingError("external-review-owner-identity-conflict")
    install = Path(__file__).resolve().parents[2]
    if (_install_identity(install) != owned["install_sha256"]
            or _sha(Path(__file__).read_bytes()) != manifest["tool_sha256"]
            or _inventory_sha(_inventory(owned["checkpoint"])) != owned["checkpoint_sha256"]):
        raise PendingError("external-review-owner-resource-drift")
    original = Path(owned["original_backup"])
    if original.exists() and _inventory_sha(_inventory(original)) != owned["source_sha256"]:
        raise PendingError("external-review-original-backup-drift")
    if owned["phase"] in {"prepared", "verified", "adopt-intent"}:
        source_carrier = original if original.exists() else Path(owned["source"])
        candidate_carrier = Path(owned["candidate"])
    elif owned["phase"] == "original-backed-up":
        source_carrier, candidate_carrier = original, Path(owned["candidate"])
        if not candidate_carrier.exists(): candidate_carrier = Path(owned["source"])
    elif owned["phase"] in {"candidate-promoted", "adopted", "restore-intent"}:
        source_carrier, candidate_carrier = original, Path(owned["source"])
    else:
        source_carrier, candidate_carrier = original, Path(owned["adopted_backup"])
    if (_inventory_sha(_inventory(source_carrier)) != owned["source_sha256"]
            or _inventory_sha(_inventory(candidate_carrier)) != owned["candidate_sha256"]):
        raise PendingError("external-review-owner-physical-drift")
    if owned["phase"] == "restored" and _inventory_sha(_inventory(owned["source"])) != owned["checkpoint_sha256"]:
        raise PendingError("external-review-restored-source-drift")
    return owner, owned

def _validate_reference_graph(job, state, reference, visited=None, depth=0):
    visited = visited if visited is not None else set()
    _evidence_ref(job, state, reference)
    target = _evidence_path(job, state, reference["path"])
    key = (str(Path(job)), str(target), reference["sha256"])
    if key in visited: return
    if depth > 64 or len(visited) >= 4096: raise PendingError("evidence-reference-graph-limit")
    visited.add(key)
    if target.suffix != ".json": return
    value = _read_json(target)
    owner_job, owner_state = _external_receipt_context(target, value, job, state)
    def walk(node, nesting):
        if nesting > 64: raise PendingError("evidence-json-depth-limit")
        if type(node) is dict:
            if set(node) == {"path", "sha256"} and type(node.get("path")) is str:
                _validate_reference_graph(owner_job, owner_state, node, visited, depth + 1)
            else:
                for child in node.values(): walk(child, nesting + 1)
        elif type(node) is list:
            for child in node: walk(child, nesting + 1)
    walk(value, 0)

def _record_ref(job, state, relative):
    ref = _ref(job, relative)
    prior = [x for x in state["receipts"] if x["path"] == ref["path"]]
    if prior and prior[0] != ref: raise PendingError("receipt-changed:" + ref["path"])
    if not prior: state["receipts"].append(ref)
    return ref

def _store_external(job, relative, data):
    rel = PurePosixPath(relative)
    if rel.is_absolute() or not rel.parts or any(part in {"", ".", ".."} for part in rel.parts):
        raise MigrationError("unsafe-job-evidence-path")
    target = Path(job).joinpath(*rel.parts)
    if target.is_symlink(): raise MigrationError("unsafe-job-evidence-path")
    if target.exists():
        if not target.is_file(): raise MigrationError("unsafe-job-evidence-path")
        if target.read_bytes() != data: raise PendingError("evidence-already-bound-to-different-bytes:" + rel.as_posix())
        return _ref(job, rel.as_posix())
    _atomic(target, data)
    return _ref(job, rel.as_posix())

def _revalidate_authority_data(job, state):
    manifest = _manifest(Path(job) / "manifest.json", allow_source_missing=True)
    if (manifest["operation_id"] != state["operation_id"] or _sha(_canonical(manifest["context"])) != state["context_sha256"]
            or manifest["source"]["path"] != state["source"] or manifest["source"]["sha256"] != state["source_sha256"]
            or state["checkpoint_sha256"] != state["source_sha256"]
            or manifest["install_sha256"] != state["install_sha256"] or manifest["catalog_sha256"] != state["catalog_sha256"]
            or manifest["context"]["boundary"]["source_receipt_sha256"] != state["boundary_sha256"]):
        raise PendingError("job-manifest-context-drift")
    install = Path(__file__).resolve().parents[2]
    if _install_identity(install) != state["install_sha256"] or _sha(Path(__file__).read_bytes()) != manifest["tool_sha256"]:
        raise PendingError("install-resource-drift")
    catalog = _validate_catalog(_read_json(install / "references" / "guides" / CATALOG_NAME))
    if _sha(_canonical(catalog)) != state["catalog_sha256"]:
        raise PendingError("catalog-drift")
    if _inventory_sha(_inventory(state["checkpoint"])) != state["checkpoint_sha256"]:
        raise PendingError("checkpoint-drift")
    backup = Path(state["original_backup"])
    if backup.exists() and _inventory_sha(_inventory(backup)) != state["source_sha256"]:
        raise PendingError("original-backup-drift")
    visited = set()
    for ref in state["receipts"]:
        try: _validate_reference_graph(job, state, ref, visited)
        except MigrationError as exc: raise PendingError("receipt-drift:" + ref["path"]) from exc
    admission_path = Path(job) / "receipts" / "admission.json"
    if admission_path.is_file() and not admission_path.is_symlink():
        admission = _read_json(admission_path)
        _exact_keys(admission, {"schema", "reviewer", "candidate_sha256", "source_sha256", "catalog_sha256", "review", "evidence"}, "admission")
        if admission["schema"] != "tackle-migration-admission/1" or admission["candidate_sha256"] != state["candidate_sha256"] or admission["source_sha256"] != state["source_sha256"] or admission["catalog_sha256"] != state["catalog_sha256"]:
            raise PendingError("admission-binding-drift")
        for ref in admission["evidence"]:
            _evidence_ref(job, state, ref)
    return manifest, catalog

def _revalidate_authority(job, state):
    try:
        return _revalidate_authority_data(job, state)
    except (MigrationError, OSError, ValueError, KeyError, TypeError) as exc:
        raise PendingError("existing-operation-authority-conflict:" + str(exc)) from exc

def _validate_boundary(job, state, *, record=True):
    path = Path(job) / "boundary.json"
    if path.is_symlink() or not path.is_file(): raise PendingError("boundary-receipt-missing")
    receipt = _read_json(path)
    _exact_keys(receipt, {"schema", "source_sha256", "at_boundary", "quiescence", "observer", "evidence"}, "boundary")
    if receipt["schema"] != "tackle-migration-boundary/1" or receipt["source_sha256"] != state["source_sha256"]:
        raise PendingError("boundary-source-mismatch")
    if type(receipt["at_boundary"]) is not bool or not receipt["at_boundary"] or receipt["quiescence"] != "observed-stopped":
        raise PendingError("boundary-or-quiescence-pending")
    if type(receipt["observer"]) is not str or not receipt["observer"].strip() or type(receipt["evidence"]) is not list:
        raise PendingError("boundary-evidence-incomplete")
    for ref in receipt["evidence"]:
        _validate_reference_graph(job, state, ref)
    if _sha(_canonical(receipt)) != state["boundary_sha256"]:
        raise PendingError("boundary-receipt-hash-mismatch")
    manifest = _manifest(Path(job) / "manifest.json", allow_source_missing=True)
    if manifest["context"]["boundary"]["at_boundary"] is not True:
        raise PendingError("context-not-at-boundary")
    return _record_ref(job, state, "boundary.json") if record else _ref(job, "boundary.json")

def _check_native(install, cwd, workspace_name, job, stage, workspace, source_hash, catalog_hash, install_hash_expected):
    install = Path(install); cwd = Path(cwd); workspace = Path(workspace)
    script = install / "scripts" / "lint.py"
    source = script.read_bytes(); source_hash_actual = _sha(source)
    rowspec = canonical_rows(source, source_hash_actual, workspace_name)
    checks = []
    before = _inventory_sha(_inventory(workspace))
    for row in range(1, 20):
        argv = [sys.executable, "-I", str(script), "--row", str(row), workspace_name]
        prefix = "receipts/" + stage + "/row-%02d-" % row
        result_path = Path(job) / (prefix + "result.json")
        if result_path.exists():
            prior = _read_json(result_path)
            if (prior.get("argv") != argv or prior.get("cwd") != str(cwd)
                    or prior.get("workspace_sha256_before") != before or prior.get("workspace_sha256_after") != before):
                raise PendingError("existing-native-capture-conflict")
            checks.append({"row": row, "result": _ref(job, prefix + "result.json")})
            continue
        if any((Path(job) / (prefix + stream)).exists() for stream in ("stdout.bin", "stderr.bin")):
            raise PendingError("interrupted-native-capture-unresolved")
        started = time.time(); monotonic = time.monotonic(); timed_out = False; launch_error = None
        proc = None; stdout = stderr = b""
        try:
            proc = subprocess.Popen(argv, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            try:
                stdout, stderr = proc.communicate(timeout=300)
            except subprocess.TimeoutExpired:
                timed_out = True
                with contextlib.suppress(ProcessLookupError): os.killpg(proc.pid, signal.SIGTERM)
                try: stdout, stderr = proc.communicate(timeout=0.5)
                except subprocess.TimeoutExpired:
                    with contextlib.suppress(ProcessLookupError): os.killpg(proc.pid, signal.SIGKILL)
                    stdout, stderr = proc.communicate(timeout=0.5)
        except OSError as exc:
            launch_error = str(exc); stdout = stderr = b""
        ended = time.time(); child_exit = proc.returncode if proc is not None and proc.returncode is not None else 127
        child_signal = -child_exit if child_exit < 0 else None
        prefix = "receipts/" + stage + "/row-%02d-" % row
        stdout_ref = _store_external(job, prefix + "stdout.bin", stdout)
        stderr_ref = _store_external(job, prefix + "stderr.bin", stderr)
        after = _inventory_sha(_inventory(workspace))
        record = {"child_exit": child_exit, "timeout": timed_out, "launch_error": launch_error,
                  "signal": child_signal, "inputs_stable": before == after and _install_identity(install) == install_hash_expected,
                  "artifacts_present": True}
        verdict = lint_verdict(row, record, stdout, stderr)
        result = {"row": row, "argv": argv, "cwd": str(cwd), "start": started, "end": ended,
                  "runtime": time.monotonic() - monotonic, "actor": str(getattr(os, "getuid", lambda: "unknown")()),
                  "script_sha256": source_hash_actual, "command_sha256": rowspec[row]["command_sha256"],
                  "exit": child_exit, "child_exit": child_exit, "signal": child_signal, "timeout": timed_out,
                  "launch_error": launch_error, "complete": not timed_out and launch_error is None,
                  "inputs_stable": record["inputs_stable"], "artifacts_present": True,
                  "verdict": verdict, "stdout": stdout_ref, "stderr": stderr_ref,
                  "workspace": str(workspace), "workspace_sha256_before": before, "workspace_sha256_after": after,
                  "install_sha256": _install_identity(install), "catalog_sha256": catalog_hash, "source_sha256": source_hash}
        result_ref = _store_external(job, prefix + "result.json", _canonical(result))
        checks.append({"row": row, "result": result_ref})
    return checks

def _dated_history(data, date, operation_id, source_hash, target, revision):
    try:
        text = data.decode("utf-8")
        lines = schema.unfenced_lines(text, strict=True)
    except (UnicodeError, ValueError) as exc: raise PendingError("history-invalid-text-or-fence") from exc
    if "\r" in text or not data.endswith(b"\n"): raise PendingError("history-final-line-not-terminated")
    dates = []
    real = []
    for line in lines:
        if line.lstrip().startswith(">") or line.startswith(("    ", "\t")): continue
        match = re.match(r"^## (\d{4}-\d\d-\d\d)(?:\s|$)", line)
        if match:
            try: datetime.date.fromisoformat(match[1])
            except ValueError as exc: raise PendingError("history-date-invalid") from exc
            dates.append(match[1])
        real.append(line)
    if dates != sorted(dates): raise PendingError("history-date-order-conflict")
    event = ("\n## " + date + " · Compact migration candidate\n\n- Prepared candidate: operation "
             + operation_id + "; source sha256 " + source_hash + "; target Tackle " + target
             + "; catalog revision " + str(revision) + ".\n").encode("utf-8")
    heading = "## " + date + " · Compact migration candidate"
    payload = event.decode("utf-8").splitlines()[-1]
    occurrences = sum(1 for index, line in enumerate(real) if line == heading
                      and real[index + 1:index + 3] == ["", payload])
    operation_lines = [line for line in real if line.startswith("- Prepared candidate: operation " + operation_id + ";")]
    if operation_lines and (operation_lines != [payload] or occurrences != 1):
        raise PendingError("conflicting-history-operation-marker")
    if occurrences:
        if occurrences != 1 or not data.endswith(event): raise PendingError("conflicting-history-operation-marker")
        return data, {"before_sha256": _sha(data[:-len(event)]), "after_sha256": _sha(data), "event_sha256": _sha(event)}
    if dates and date < dates[-1]: raise PendingError("history-date-order-conflict")
    return data + event, {"before_sha256": _sha(data), "after_sha256": _sha(data + event), "event_sha256": _sha(event)}

def _history_usage_prefix_findings(expected, current):
    findings = []
    for name in ("history.md", "resource-usage.md"):
        if name in expected and (name not in current or not current[name].startswith(expected[name])):
            findings.append("preserved-byte-prefix-drift:" + name)
    return findings

def _transformed_checkpoint(state, manifest):
    return _adapter_chain(_tree(state["checkpoint"]), manifest["observed"]["methodology"], manifest["context"])

def _append_marker_and_stamp(candidate, state, manifest, catalog, job):
    candidate = Path(candidate)
    with _context_lock(candidate, required=True):
        files = _tree(candidate)
        _supported_methodology(files, catalog["target_methodology"])
        expected = _transformed_checkpoint(state, manifest)
        prefix_findings = _history_usage_prefix_findings(expected, files)
        if prefix_findings: raise PendingError(";".join(prefix_findings))
        history = files.get("history.md")
        if history is None: raise PendingError("existing-history-carrier-required")
        new_history, marker = _dated_history(history, manifest["context"]["date"], state["operation_id"], state["source_sha256"], catalog["target_methodology"], catalog["revision"])
        agents = files.get("AGENTS.md")
        stamped = agents
        if agents is not None:
            try: text = agents.decode("utf-8")
            except UnicodeError as exc: raise PendingError("methodology-file-not-utf8") from exc
            stamped = schema.set_methodology(text, "Tackle " + catalog["target_methodology"]).encode("utf-8")
        # Seal the exact allowed transition before its first effect. A resumed
        # transition recognizes only those recorded whole-tree states.
        transition_path = Path(job) / "receipts/transition.json"
        if transition_path.exists():
            transition = _read_json(transition_path)
            _exact_keys(transition, {"schema", "operation_id", "marker", "allowed_inventory_sha256", "before_inventory", "final_inventory", "history_before", "history_after"}, "transition")
            if transition["schema"] != "tackle-migration-transition/1" or transition["operation_id"] != state["operation_id"]:
                raise PendingError("marker-transition-operation-conflict")
            _validate_reference_graph(job, state, transition["history_before"])
            _validate_reference_graph(job, state, transition["history_after"])
            current = _inventory_sha(_inventory(candidate))
            if current not in transition["allowed_inventory_sha256"]:
                raise PendingError("marker-transition-inventory-conflict")
            marker = transition["marker"]
            if _sha(history) not in {marker["before_sha256"], marker["after_sha256"]}:
                raise PendingError("marker-transition-history-conflict")
        else:
            if new_history == history: raise PendingError("unbound-existing-history-marker")
            before_inventory = _inventory(candidate)
            history_inventory = dict(before_inventory)
            history_inventory["history.md"] = dict(history_inventory["history.md"], sha256=_sha(new_history))
            final_inventory = dict(history_inventory)
            if agents is not None: final_inventory["AGENTS.md"] = dict(final_inventory["AGENTS.md"], sha256=_sha(stamped))
            transition = {"schema": "tackle-migration-transition/1", "operation_id": state["operation_id"],
                          "marker": marker, "allowed_inventory_sha256": [_inventory_sha(i) for i in (before_inventory, history_inventory, final_inventory)],
                          "before_inventory": before_inventory, "final_inventory": final_inventory,
                          "history_before": _store_external(job, "receipts/history-before.bin", history),
                          "history_after": _store_external(job, "receipts/history-after.bin", new_history)}
            _store_external(job, "receipts/transition.json", _canonical(transition))
        expected_history = (Path(job) / transition["history_after"]["path"]).read_bytes()
        before_history = (Path(job) / transition["history_before"]["path"]).read_bytes()
        reproduced, expected_marker = _dated_history(before_history, manifest["context"]["date"], state["operation_id"], state["source_sha256"], catalog["target_methodology"], catalog["revision"])
        if reproduced != expected_history or expected_marker != marker:
            raise PendingError("marker-transition-content-conflict")
        if history != expected_history:
            if _sha(history) != marker["before_sha256"]: raise PendingError("history-preappend-conflict")
            _atomic_preserve(candidate / "history.md", expected_history)
        # Marker publication is prior to the deliberate Methodology transition.
        marker_ref = _store_external(job, "receipts/marker.json", _canonical({"schema": "tackle-migration-marker/1", "path": str(candidate / "history.md"), "operation_id": state["operation_id"], "target_methodology": catalog["target_methodology"], "revision": catalog["revision"], **marker}))
        if agents is not None and stamped != agents:
            _atomic_preserve(candidate / "AGENTS.md", stamped)
        if _inventory(candidate) != transition["final_inventory"]:
            raise PendingError("marker-stamp-postinventory-conflict")
    return marker_ref

def _atomic_preserve(path, data):
    path = Path(path)
    if path.is_symlink() or not path.is_file(): raise PendingError("candidate-carrier-not-regular")
    mode = stat.S_IMODE(path.lstat().st_mode)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path); _fsync_dir(path.parent)
    except BaseException:
        with contextlib.suppress(OSError): os.unlink(temporary)
        raise

def _semantic_review(job, state, manifest):
    path = Path(job) / "semantic-review.json"
    if path.is_symlink() or not path.is_file(): return None, ["semantic-review.json"]
    review = _read_json(path)
    _exact_keys(review, {"schema", "reviewer", "candidate_sha256", "source_sha256", "catalog_sha256", "decisions"}, "semantic-review")
    if review["schema"] != "tackle-migration-review/1" or type(review["reviewer"]) is not str or not review["reviewer"].strip():
        raise PendingError("semantic-review-identity-invalid")
    if (review["candidate_sha256"] != state["candidate_sha256"] or review["source_sha256"] != state["source_sha256"]
            or review["catalog_sha256"] != state["catalog_sha256"]):
        raise PendingError("stale-semantic-review")
    applicable = {row["id"] for row in manifest["obligations"] if row["state"] != "not-applicable" and (row["kind"] == "required" or row["family"] in manifest["context"]["optional_requests"])}
    physical = {row["id"] for row in manifest["obligations"] if row["family"] in {"S", "A", "V", "Z"} and row["id"] in applicable}
    expected = applicable - physical
    decisions = review["decisions"]
    if type(decisions) is not list: raise PendingError("semantic-decisions-not-list")
    by_id = {}
    for decision in decisions:
        _exact_keys(decision, {"id", "state", "evidence"}, "semantic-decision")
        if type(decision["id"]) is not str or decision["id"] in by_id: raise PendingError("duplicate-semantic-decision")
        if decision["state"] not in {"satisfied", "pending", "unknown"} or type(decision["evidence"]) is not list:
            raise PendingError("invalid-semantic-decision")
        by_id[decision["id"]] = decision
    # A valid causal unresolved row must remain visible before global coverage,
    # unrelated evidence or native failures. It can never grant admission.
    visited = set()
    unresolved = [ident for ident, row in by_id.items() if ident in applicable and row["state"] in {"pending", "unknown"}]
    for ident in unresolved:
        for ref in by_id[ident]["evidence"]:
            try: _validate_reference_graph(job, state, ref, visited)
            except MigrationError as exc: raise PendingError("semantic-evidence-drift:" + ident) from exc
    if unresolved: return review, sorted(unresolved)
    if frozenset(by_id) not in {frozenset(expected), frozenset(applicable)}:
        return review, sorted((expected - set(by_id)) | (set(by_id) - applicable))
    pending = []
    for ident, decision in by_id.items():
        if not decision["evidence"]: pending.append(ident)
        for ref in decision["evidence"]:
            try: _validate_reference_graph(job, state, ref, visited)
            except MigrationError as exc: raise PendingError("semantic-evidence-drift:" + ident) from exc
    return review, pending

def _native_results(job, state, capture, workspace, cwd, stage, expected_hash):
    _exact_keys(capture, {"schema", "stage", "workspace", "cwd", "source_sha256", "candidate_sha256", "install_sha256", "catalog_sha256", "checks"}, "capture")
    if (capture["schema"] != "tackle-migration-capture/1" or capture["stage"] != stage
            or capture["workspace"] != str(workspace) or capture["cwd"] != str(cwd)
            or capture["candidate_sha256"] != expected_hash
            or capture["source_sha256"] != state["source_sha256"]
            or capture["install_sha256"] != state["install_sha256"] or capture["catalog_sha256"] != state["catalog_sha256"]):
        raise PendingError("native-capture-binding-conflict:" + stage)
    if type(capture["checks"]) is not list or [x.get("row") for x in capture["checks"]] != list(range(1, 20)):
        raise PendingError("native-capture-row-coverage:" + stage)
    script = Path(__file__).resolve().parents[2] / "scripts/lint.py"
    script_hash = _sha(script.read_bytes())
    rows = canonical_rows(script.read_bytes(), script_hash, Path(workspace).name)
    results = []
    for check in capture["checks"]:
        _exact_keys(check, {"row", "result"}, "native-check")
        _validate_reference_graph(job, state, check["result"])
        result = _read_json(_evidence_path(job, state, check["result"]["path"]))
        number = check["row"]
        if (result["row"] != number or result["argv"] != [sys.executable, "-I", str(script), "--row", str(number), Path(workspace).name]
                or result["cwd"] != str(cwd) or result["workspace"] != str(workspace)
                or result["script_sha256"] != script_hash or result["command_sha256"] != rows[number]["command_sha256"]
                or result["source_sha256"] != state["source_sha256"] or result["catalog_sha256"] != state["catalog_sha256"]
                or result["install_sha256"] != state["install_sha256"]
                or type(result["exit"]) is not int or result["exit"] != result["child_exit"]
                or result["workspace_sha256_before"] != expected_hash or result["workspace_sha256_after"] != expected_hash):
            raise PendingError("native-child-binding-conflict:" + stage + ":" + str(number))
        stdout = _evidence_path(job, state, result["stdout"]["path"]).read_bytes()
        stderr = _evidence_path(job, state, result["stderr"]["path"]).read_bytes()
        record = {key: result[key] for key in ("timeout", "launch_error", "signal", "inputs_stable", "artifacts_present")}
        record["child_exit"] = result["exit"]
        verdict = lint_verdict(number, record, stdout, stderr)
        if verdict != result["verdict"]: raise PendingError("native-verdict-drift")
        results.append(result)
    return results

def _capture_stage(job, state, workspace, stage, name):
    workspace = Path(workspace); cwd = workspace.parents[2]
    expected_hash = _inventory_sha(_inventory(workspace))
    path = Path(job) / "receipts" / name
    if path.exists():
        capture = _read_json(path)
    else:
        checks = _check_native(Path(__file__).resolve().parents[2], cwd, workspace.name, job, stage, workspace,
                               state["source_sha256"], state["catalog_sha256"], state["install_sha256"])
        capture = {"schema": "tackle-migration-capture/1", "stage": stage, "workspace": str(workspace), "cwd": str(cwd),
                   "source_sha256": state["source_sha256"], "candidate_sha256": expected_hash,
                   "install_sha256": state["install_sha256"], "catalog_sha256": state["catalog_sha256"], "checks": checks}
        _store_external(job, "receipts/" + name, _canonical(capture))
    _native_results(job, state, capture, workspace, cwd, stage, expected_hash)
    return _record_ref(job, state, "receipts/" + name)

def _readiness(candidate, manifest, native):
    files = _tree(candidate)
    bucket = schema.schema_of(files)
    failures, observations = [], []
    if bucket not in {"5", "lite"}: failures.append("current-structure-required")
    Context(candidate)  # Read-only constructor checks the installed current layout.
    _, quality, states = _board_observation(files)
    status = dict(states)
    if bucket != "lite" and quality != "observed": failures.append("current-board-unknown")
    bindings = _declared_briefs(files)
    for task in manifest["context"]["next_wave"]:
        path = _brief_path(files, task, bindings)
        fields = _current_fields(files[path])
        text = schema.decode(files[path])
        gaps = []
        if status.get(task) not in {"Draft", "Ready to run"}: gaps.append("not-unstarted")
        if fields.get("Detail") != "full": gaps.append("full-next-wave-contract-required")
        if not fields.get("Write scope", "").strip(): gaps.append("missing-write-scope")
        acceptance = re.search(r"(?m)^## (?:Acceptance check|Acceptance and recovery|Check)(?:\s|$)", text)
        if acceptance is None: gaps.append("missing-acceptance-check")
        else:
            section = text[acceptance.end():]
            section = re.split(r"(?m)^## ", section, maxsplit=1)[0]
            if not re.search(r"(?ms)^```(?:sh|bash|shell)?\s*\n\S.*?^```\s*$", section):
                gaps.append("missing-acceptance-command")
        if (not fields.get("Related regression check", "").strip()
                and not re.search(r"(?m)^## (?:Regression check|Regression checks)(?:\s|$)", text)):
            gaps.append("missing-regression-check")
        dependencies = []
        for dep in re.findall(r"T-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", fields.get("Depends on", "")):
            dependencies.append({"task": dep, "state": status.get(dep, "unknown")})
            if status.get(dep) != "Complete": gaps.append("dependency-not-complete:" + dep)
        observations.append({"task": task, "path": path, "sha256": _sha(files[path]), "fields": fields,
                             "board_state": status.get(task), "dependencies": dependencies, "findings": gaps})
        failures.extend(task + ":" + gap for gap in gaps)
    # These are the actual current installed read-only dependency/seal consumers.
    selected_native = [{"row": result["row"], "verdict": result["verdict"]} for result in native if result["row"] in {2, 7, 18, 19}]
    if len(selected_native) != 4 or any(row["verdict"] != "PASS" for row in selected_native): failures.append("native-readiness-findings")
    return {"schema": "tackle-migration-readiness/1", "source_sha256": manifest["source"]["sha256"],
            "candidate_sha256": _inventory_sha(_inventory(candidate)), "bucket": bucket,
            "next_wave": observations, "native_readonly": selected_native, "findings": failures}

def _brief_receipt_lines(data):
    lines = [line for line in schema.unfenced_lines(schema.decode(data), strict=True)
             if not line.lstrip().startswith(">")]
    baselines, errata = [], []
    for line in lines:
        if line.startswith("**Brief sha256**:"):
            match = re.fullmatch(r"\*\*Brief sha256\*\*:\s*([0-9a-f]{64})\s*", line)
            if match is None: return None
            baselines.append((match[1], line))
        elif line.startswith("**Brief erratum**:"):
            match = re.fullmatch(r"\*\*Brief erratum\*\*:\s*(D-[0-9]+)\s+·\s+sha256\s+([0-9a-f]{64})\s*", line)
            if match is None: return None
            errata.append((match[1], match[2], line))
    return baselines, errata

def _history_brief_baselines(files, task):
    values = []
    prefix = "Brief sha256 " + task + ":"
    for name in ("history-archive.md", "history.md"):
        if name not in files: continue
        for line in schema.unfenced_lines(schema.decode(files[name]), strict=True):
            if line.startswith(("- ", "* ")): line = line[2:]
            if line.startswith(prefix):
                value = line[len(prefix):].strip()
                if not re.fullmatch(r"[0-9a-f]{64}", value): return None
                values.append(value)
    return values

def _closed_erratum_authorized(job, state, manifest, expected, current, task, path, native):
    """The existing R receipt/decision/row14 consumers permit only this delta.

    Identity and byte checks are mechanical. The required independent R review
    owns whether the active decision authorized this edit before it occurred.
    """
    report = "reports/" + task + "-report.md"
    if report not in expected or report not in current or path not in current: return False
    prior_records = _brief_receipt_lines(expected[report])
    current_records = _brief_receipt_lines(current[report])
    if prior_records is None or current_records is None: return False
    prior_baselines, prior_errata = prior_records
    baselines, errata = current_records
    if len(prior_baselines) > 1 or len(baselines) != 1: return False
    if prior_baselines and baselines != prior_baselines: return False
    # Keep every prior erratum literally; one new edit adds its one new receipt.
    if len(errata) != len(prior_errata) + 1 or errata[:-1] != prior_errata: return False
    old_hash, new_hash = _sha(expected[path]), _sha(current[path])
    history_before = _history_brief_baselines(expected, task)
    history_now = _history_brief_baselines(current, task)
    if history_before is None or history_now is None or len(history_before) > 1 or len(history_now) != 1: return False
    baseline = prior_baselines[0][0] if prior_baselines else history_before[0] if history_before else old_hash
    if baselines[0][0] != baseline or history_now[0] != baseline: return False
    if (prior_errata[-1][1] if prior_errata else baseline) != old_hash: return False
    decision, after_hash, literal = errata[-1]
    if after_hash != new_hash or not current[report].endswith((literal + "\n").encode("utf-8")): return False
    decisions = current.get("decisions.md")
    if decisions is None: return False
    headings = [line for line in schema.unfenced_lines(schema.decode(decisions), strict=True)
                if re.match(r"^## " + re.escape(decision) + r"(?:\s|$)", line)]
    if len(headings) != 1 or "✅ active" not in headings[0] or "superseded by" in headings[0].casefold() or "⤴" in headings[0]: return False
    if not any(result["row"] == 14 and result["verdict"] == "PASS" for result in native): return False
    # The baseline is already present in the sealed pre-event history, and the
    # immutable checkpoint carries its exact actual pre-edit brief bytes.
    transition = _read_json(Path(job) / "receipts/transition.json")
    _validate_reference_graph(job, state, transition["history_before"])
    pre_event_history = _evidence_path(job, state, transition["history_before"]["path"]).read_bytes()
    if _history_brief_baselines({"history.md": pre_event_history,
                                 **({"history-archive.md": current["history-archive.md"]} if "history-archive.md" in current else {})}, task) != [baseline]:
        return False
    review_path = Path(job) / "semantic-review.json"
    if review_path.is_symlink() or not review_path.is_file(): return False
    review = _read_json(review_path)
    _exact_keys(review, {"schema", "reviewer", "candidate_sha256", "source_sha256", "catalog_sha256", "decisions"}, "semantic-review")
    if (review["schema"] != "tackle-migration-review/1" or review["candidate_sha256"] != state["candidate_sha256"]
            or review["source_sha256"] != state["source_sha256"] or review["catalog_sha256"] != state["catalog_sha256"]
            or type(review["reviewer"]) is not str or not review["reviewer"].strip() or type(review["decisions"]) is not list):
        return False
    required_r = {row["id"] for row in manifest["obligations"] if row["family"] == "R" and row["state"] != "not-applicable"}
    if not required_r: return False
    by_id = {}
    for row in review["decisions"]:
        _exact_keys(row, {"id", "state", "evidence"}, "semantic-decision")
        if row["id"] in by_id: return False
        by_id[row["id"]] = row
    visited = set()
    for ident in required_r:
        row = by_id.get(ident)
        if row is None or row["state"] != "satisfied" or type(row["evidence"]) is not list or not row["evidence"]: return False
        for reference in row["evidence"]: _validate_reference_graph(job, state, reference, visited)
    return True

def _closed_report_body_preserved(before, after, status):
    """Permit only the existing missing Complete-report receipt, never body repair.

    This is physical shape, not knowledge of the Remains value. Actual lint and
    the separately bound R semantic review remain required before admission.
    """
    def project(data):
        kept, remains, fence = [], [], None
        for raw in data.splitlines(keepends=True):
            line = schema.decode(raw).rstrip("\r\n")
            delimiter = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
            if fence:
                if (delimiter and delimiter[1][0] == fence[0]
                        and len(delimiter[1]) >= fence[1] and not delimiter[2].strip()):
                    fence = None
                kept.append(raw)
                continue
            if delimiter:
                fence = (delimiter[1][0], len(delimiter[1]))
                kept.append(raw)
                continue
            if not line.lstrip().startswith(">"):
                # Their exact grammar, identity and ordering are checked below
                # by the unchanged baseline/erratum consumers, not inferred here.
                if line.startswith(("**Brief sha256**:", "**Brief erratum**:")):
                    continue
                if re.match(r"^[ \t]*(?:[-*+][ \t]+)?\*\*Remains\*\*:", line):
                    remains.append(line)
            kept.append(raw)
        return (None if fence else b"".join(kept)), remains

    original, prior = project(before)
    current, receipts = project(after)
    if original is None or current is None:
        return False
    if current == original:
        return True
    if status != "Complete" or prior or len(receipts) != 1:
        return False
    receipt = receipts[0]
    if not re.fullmatch(r"[ \t]*(?:[-*+][ \t]+)?\*\*Remains\*\*:[ \t]*(?:none|O-[0-9]{2}(?:[ \t]*,[ \t]*O-[0-9]{2})*)[ \t]*", receipt):
        return False
    if not current.startswith(original):
        return False
    suffix = current[len(original):]
    if not original.endswith(b"\n") and not suffix.startswith(b"\n"):
        return False
    return suffix.strip(b"\n") == receipt.encode("utf-8")

def _physical_findings(job, state, manifest, catalog):
    candidate = Path(state["candidate"])
    checkpoint = Path(state["checkpoint"])
    original = _tree(checkpoint); current = _tree(candidate)
    source_inventory = _inventory(checkpoint)
    directories = {path: dict(meta) for path, meta in source_inventory.items() if meta["type"] == "directory"}
    expected = _adapter_chain(original, manifest["observed"]["methodology"], manifest["context"], directories=directories)
    failures = {family: [] for family in ("S", "A", "V", "Z")}
    _supported_methodology(original, catalog["target_methodology"])
    _supported_methodology(current, catalog["target_methodology"])
    failures["A"].extend(_history_usage_prefix_findings(expected, current))
    candidate_root = candidate.parents[2]
    pre = _read_json(Path(job) / "receipts/pre-stamp.json")
    post = _read_json(Path(job) / "receipts/post-stamp.json")
    transition = _read_json(Path(job) / "receipts/transition.json")
    pre_results = _native_results(job, state, pre, candidate, candidate_root, "pre-stamp", _inventory_sha(transition["before_inventory"]))
    post_results = _native_results(job, state, post, candidate, candidate_root, "post-stamp", state["candidate_sha256"])
    if _inventory_sha(_inventory(checkpoint)) != state["checkpoint_sha256"]: failures["S"].append("checkpoint-drift")
    if schema.schema_of(current) not in {"5", "lite"}: failures["S"].append("target-structure-missing")
    try: Context(candidate)
    except ValueError as exc: failures["A"].append(str(exc))
    # Opaque records, snapshots and directories retain their original bytes/modes;
    # only the declared current procedure carriers may have operator preparation.
    allowed = {"AGENTS.md", "task-board.md", "plan.md", "design-contract.md", "decisions.md", "questions.md", "reference.md",
               "history.md", "resource-usage.md", "current-work.md", "handoff-brief.md", "map-delta.json", "requirements-delta.md",
               "plan-view.html", "plan-view.stamp.js", ".context-lock"}
    bindings = _declared_briefs(expected)
    _, _, old_states = _board_observation(expected)
    for task, status in old_states:
        path = _brief_path(expected, task, bindings, required=False)
        if status not in {"Complete", "Skipped", "Unverifiable"} and path: allowed.add(path)
        if status in {"Complete", "Skipped", "Unverifiable"} and path and current.get(path) != expected.get(path):
            if _closed_erratum_authorized(job, state, manifest, expected, current, task, path, post_results):
                allowed.add(path)
            else:
                failures["A"].append("closed-brief-changed-without-authorized-erratum:" + task)
        report = "reports/" + task + "-report.md"
        if report in expected:
            # Existing baseline/erratum semantics are checked by real row14 and
            # independent review; dropping any prior report bytes is forbidden.
            if report not in current or not _closed_report_body_preserved(expected[report], current[report], status):
                failures["A"].append("historical-report-rewritten:" + task)
            else:
                prior_receipts = _brief_receipt_lines(expected[report])
                receipts = _brief_receipt_lines(current[report])
                if prior_receipts is None or receipts is None:
                    failures["A"].append("historical-report-receipt-invalid:" + task)
                elif ((prior_receipts[0] and receipts[0] != prior_receipts[0])
                      or receipts[1][:len(prior_receipts[1])] != prior_receipts[1]):
                    failures["A"].append("historical-report-receipt-rewritten:" + task)
            allowed.add(report)
    for path, data in expected.items():
        if path not in allowed and current.get(path) != data: failures["A"].append("preserved-bytes-drift:" + path)
    mapped_inventory = _transformed_inventory(original, expected, source_inventory, directories)
    current_inventory = _inventory(candidate)
    for path, meta in mapped_inventory.items():
        found = current_inventory.get(path)
        if found is None or found["type"] != meta["type"] or found["mode"] != meta["mode"]:
            failures["S"].append("preserved-type-or-mode-drift:" + path)
    _, quality, current_states = _board_observation(current)
    if old_states != current_states: failures["A"].append("migration-changed-task-state")
    if schema.schema_of(expected) == "lite":
        source_state, candidate_state = _lite_state(expected), _lite_state(current)
        if source_state not in {"Ready", "running", "blocked"} or candidate_state != source_state:
            failures["A"].append("lite-state-unknown-closed-or-changed")
    if manifest["observed"]["classification"] == "unknown": failures["A"].append("workspace-closure-or-state-unknown")
    for label, results in (("pre-stamp", pre_results), ("post-stamp", post_results)):
        for result in results:
            allowed_verdicts = {"PASS", "WARN"} if result["row"] in {8, 13, 15} else {"PASS"}
            if result["verdict"] not in allowed_verdicts:
                failures["V"].append(label + ":row" + str(result["row"]) + ":" + result["verdict"])
    readiness = _readiness(candidate, manifest, post_results)
    failures["V"].extend(readiness["findings"])
    probe = Path(job) / "restore-probe"
    if _inventory_sha(_inventory(probe)) != state["checkpoint_sha256"]: failures["V"].append("restore-probe-drift")
    restore = _read_json(Path(job) / "receipts/restore-probe.json")
    if restore["restored_inventory_sha256"] != state["checkpoint_sha256"]: failures["V"].append("restore-probe-receipt-drift")
    marker = _read_json(Path(job) / "receipts/marker.json")
    if (marker["operation_id"] != state["operation_id"] or marker["target_methodology"] != catalog["target_methodology"]
            or marker["revision"] != catalog["revision"] or _sha(current.get("history.md", b"")) != marker["after_sha256"]
            or current_inventory != transition["final_inventory"]):
        failures["Z"].append("marker-stamp-transition-drift")
    if "AGENTS.md" in current and _methodology(current) != "Tackle " + catalog["target_methodology"]:
        failures["Z"].append("methodology-not-current")
    _dated_history(current["history.md"], manifest["context"]["date"], state["operation_id"], state["source_sha256"], catalog["target_methodology"], catalog["revision"])
    return failures, readiness

def _completed(job, state):
    """Validate a recorded terminal poststate without publishing or repairing it."""
    _revalidate_authority(job, state)
    src, candidate = Path(state["source"]), Path(state["candidate"])
    original, adopted, stage = (Path(state[key]) for key in ("original_backup", "adopted_backup", "restore_stage"))
    if state["phase"] == "adopted":
        valid = (state["operation"] == "adopt" and src.is_dir() and not candidate.exists()
                 and original.is_dir() and not adopted.exists() and not stage.exists()
                 and _inventory_sha(_inventory(src)) == state["candidate_sha256"]
                 and _inventory_sha(_inventory(original)) == state["source_sha256"])
    elif state["phase"] == "restored":
        valid = (state["operation"] == "restore" and src.is_dir() and not candidate.exists()
                 and original.is_dir() and adopted.is_dir() and not stage.exists()
                 and _inventory_sha(_inventory(src)) == state["checkpoint_sha256"]
                 and _inventory_sha(_inventory(original)) == state["source_sha256"]
                 and _inventory_sha(_inventory(adopted)) == state["candidate_sha256"])
    else: raise PendingError("operation-not-complete")
    if not valid: raise PendingError("completed-operation-mismatch")
    admission = Path(job) / "receipts/admission.json"
    if not admission.is_file() or not any(ref["path"] == "receipts/admission.json" for ref in state["receipts"]):
        raise PendingError("completed-admission-missing")
    _validate_boundary(job, state, record=False)
    manifest = _manifest(Path(job) / "manifest.json", allow_source_missing=True)
    _, pending = _semantic_review(job, state, manifest)
    if pending: raise PendingError("completed-semantic-admission-conflict")
    return 0

def _cmd_verify(args):
    job = _absolute(args.job, "job", exists=True, directory=True)
    state = _load_state(job)
    with _parent_lock(state["source"]), _existing_context_locks(state["source"], state["candidate"], state["original_backup"], state["adopted_backup"]):
        if state["phase"] in {"adopted", "restored"}: return _completed(job, state)
        with _context_lock(state["candidate"], required=True):
            return _verify_locked(job, state)

def _verify_locked(job, st):
    if st["phase"] not in {"prepared", "verified"}: raise PendingError("verify-phase-conflict")
    manifest, catalog = _revalidate_authority(job, st)
    source_path = Path(st["source"])
    if not source_path.is_dir() or _inventory_sha(_inventory(source_path)) != st["source_sha256"]:
        raise PendingError("frozen-source-drift")
    candidate = Path(st["candidate"])
    _supported_methodology(_tree(candidate), catalog["target_methodology"])
    if st["phase"] == "verified":
        if _inventory_sha(_inventory(candidate)) != st["candidate_sha256"]: raise PendingError("frozen-candidate-drift")
        _, pending = _semantic_review(job, st, manifest)
        if pending: raise PendingError("verified-semantic-admission-conflict")
        _validate_boundary(job, st, record=False)
        if not any(ref["path"] == "receipts/admission.json" for ref in st["receipts"]): raise PendingError("verified-admission-missing")
        return 0
    if not (job / "handoff.json").exists():
        source_project = job / "source-project/docs/plans" / source_path.name
        if _inventory_sha(_inventory(source_project)) != st["source_sha256"]: raise PendingError("source-diagnostic-copy-drift")
        source_ref = _capture_stage(job, st, source_project, "source-diagnostic", "source-capture.json")
        transition_path = job / "receipts/transition.json"
        if not transition_path.exists():
            _capture_stage(job, st, candidate, "pre-stamp", "pre-stamp.json")
        else:
            transition = _read_json(transition_path)
            pre = _read_json(job / "receipts/pre-stamp.json")
            _native_results(job, st, pre, candidate, candidate.parents[2], "pre-stamp", _inventory_sha(transition["before_inventory"]))
            _record_ref(job, st, "receipts/pre-stamp.json")
        _record_ref(job, st, "receipts/marker.json") if (job / "receipts/marker.json").exists() else None
        _append_marker_and_stamp(candidate, st, manifest, catalog, job)
        _record_ref(job, st, "receipts/transition.json")
        _record_ref(job, st, "receipts/marker.json")
        st["candidate_sha256"] = _inventory_sha(_inventory(candidate))
        _capture_stage(job, st, candidate, "post-stamp", "post-stamp.json")
        probe = job / "restore-probe"
        if not probe.exists(): _copy_bytes(st["checkpoint"], probe)
        if _inventory_sha(_inventory(probe)) != st["checkpoint_sha256"]: raise PendingError("restore-probe-inventory-mismatch")
        probe_workspace = job / "restore-diagnostic-project/docs/plans" / source_path.name
        if not probe_workspace.exists():
            probe_workspace.parent.mkdir(parents=True, exist_ok=True)
            _copy_bytes(probe, probe_workspace)
        if _inventory_sha(_inventory(probe_workspace)) != st["checkpoint_sha256"]: raise PendingError("restore-diagnostic-copy-drift")
        probe_ref = _capture_stage(job, st, probe_workspace, "restore-diagnostic", "restore-diagnostic.json")
        def diagnostic(ref):
            capture = _read_json(job / ref["path"])
            return [(r["row"], r["exit"], r["signal"], r["timeout"], r["verdict"])
                    for r in (_read_json(job / item["result"]["path"]) for item in capture["checks"])]
        if diagnostic(source_ref) != diagnostic(probe_ref): raise PendingError("restore-probe-native-diagnostic-mismatch")
        restore = {"schema": "tackle-migration-restore/1", "checkpoint_sha256": st["checkpoint_sha256"],
                   "restored_inventory_sha256": _inventory_sha(_inventory(probe)), "restored_workspace": str(probe),
                   "diagnostic_workspace": str(probe_workspace), "diagnostic_inventory_sha256": _inventory_sha(_inventory(probe_workspace)),
                   "diagnostic": probe_ref, "source_diagnostic": source_ref}
        _store_external(job, "receipts/restore-probe.json", _canonical(restore)); _record_ref(job, st, "receipts/restore-probe.json")
        failures, readiness = _physical_findings(job, st, manifest, catalog)
        _store_external(job, "receipts/readiness.json", _canonical(readiness)); _record_ref(job, st, "receipts/readiness.json")
        physical = {"schema": "tackle-migration-physical/1", "candidate_sha256": st["candidate_sha256"],
                    "source_sha256": st["source_sha256"], "checkpoint_sha256": st["checkpoint_sha256"],
                    "install_sha256": st["install_sha256"], "catalog_sha256": st["catalog_sha256"],
                    "findings": failures, "receipts": list(st["receipts"])}
        _store_external(job, "receipts/physical.json", _canonical(physical)); _record_ref(job, st, "receipts/physical.json")
        handoff = {"schema": "tackle-migration-handoff/1", "operation_id": st["operation_id"], "source_sha256": st["source_sha256"],
                   "candidate_sha256": st["candidate_sha256"], "checkpoint_sha256": st["checkpoint_sha256"],
                   "install_sha256": st["install_sha256"], "catalog_sha256": st["catalog_sha256"], "receipts": list(st["receipts"])}
        _store_external(job, "handoff.json", _canonical(handoff)); _record_ref(job, st, "handoff.json")
        _write_state(job, st)
    else:
        handoff = _read_json(job / "handoff.json")
        if handoff.get("operation_id") != st["operation_id"] or handoff.get("candidate_sha256") != st["candidate_sha256"]:
            raise PendingError("stale-frozen-handoff")
        if _inventory_sha(_inventory(candidate)) != st["candidate_sha256"]: raise PendingError("frozen-candidate-drift")
    # Source/candidate/resource identities are frozen before inspecting causal rows.
    review, pending = _semantic_review(job, st, manifest)
    if pending:
        for ident in pending:
            decision = next((row for row in review["decisions"] if row["id"] == ident), None) if review else None
            status = decision["state"] if decision else "unknown"
            print("pending semantic decision " + ident + " state " + status + ": semantic-review.json", file=sys.stderr)
        return 1
    failures, readiness = _physical_findings(job, st, manifest, catalog)
    if any(failures.values()):
        print("pending physical checks: " + "; ".join(family + ":" + ",".join(items) for family, items in failures.items() if items), file=sys.stderr)
        return 1
    _validate_boundary(job, st)
    _revalidate_authority(job, st)
    if (_inventory_sha(_inventory(source_path)) != st["source_sha256"]
            or _inventory_sha(_inventory(candidate)) != st["candidate_sha256"]):
        raise PendingError("frozen-source-or-candidate-drift")
    review_ref = _record_ref(job, st, "semantic-review.json")
    boundary = _read_json(job / "boundary.json")
    evidence = [ref for decision in review["decisions"] for ref in decision["evidence"]] + boundary["evidence"]
    admission = {"schema": "tackle-migration-admission/1", "reviewer": review["reviewer"], "candidate_sha256": st["candidate_sha256"],
                 "source_sha256": st["source_sha256"], "catalog_sha256": st["catalog_sha256"], "review": review_ref, "evidence": evidence}
    _store_external(job, "receipts/admission.json", _canonical(admission)); _record_ref(job, st, "receipts/admission.json")
    st["phase"] = "verified"; _write_state(job, st)
    return 0

def _cmd_adopt(args):
    job = _absolute(args.job, "job", exists=True, directory=True); st = _load_state(job)
    if st["phase"] in {"adopted", "restored"}:
        with _parent_lock(st["source"]), _existing_context_locks(st["source"], st["original_backup"], st["adopted_backup"]):
            return _completed(job, st)
    if st["operation"] != "adopt": raise PendingError("wrong-operation")
    if st["phase"] not in {"verified", "adopt-intent", "original-backed-up", "candidate-promoted", "adopted"}:
        raise PendingError("adoption-not-verified")
    src, candidate, backup = Path(st["source"]), Path(st["candidate"]), Path(st["original_backup"])
    with _parent_lock(src), _existing_context_locks(src, candidate, backup):
        if Path(st["restore_stage"]).exists() or Path(st["adopted_backup"]).exists():
            raise PendingError("adopt-unexpected-restore-carrier")
        manifest, catalog = _revalidate_authority(job, st)
        _, pending = _semantic_review(job, st, manifest)
        if pending: raise PendingError("semantic-admission-no-longer-valid")
        _validate_boundary(job, st, record=False)
        if not any(ref["path"] == "receipts/admission.json" for ref in st["receipts"]):
            raise PendingError("admission-missing")
        if candidate.exists():
            with _context_lock(candidate, required=True):
                failures, _ = _physical_findings(job, st, manifest, catalog)
                if any(failures.values()): raise PendingError("physical-admission-no-longer-valid")
        source_exists, cand_exists, backup_exists = src.exists(), candidate.exists(), backup.exists()
        src_hash = _inventory_sha(_inventory(src)) if source_exists else None
        cand_hash = _inventory_sha(_inventory(candidate)) if cand_exists else None
        backup_hash = _inventory_sha(_inventory(backup)) if backup_exists else None
        states = (source_exists, cand_exists, backup_exists)
        if states == (True, True, False) and src_hash == st["source_sha256"] and cand_hash == st["candidate_sha256"]:
            if st["phase"] not in {"verified", "adopt-intent"}: raise PendingError("adopt-physical-state-regressed")
            if st["phase"] != "adopt-intent":
                st["phase"] = "adopt-intent"; _write_state(job, st)
            os.rename(src, backup); _fsync_dir(src.parent); _fsync_dir(backup.parent)
            st["phase"] = "original-backed-up"; _write_state(job, st)
            states = (False, True, True)
        if states == (False, True, True):
            if _inventory_sha(_inventory(candidate)) != st["candidate_sha256"] or _inventory_sha(_inventory(backup)) != st["source_sha256"]:
                raise PendingError("adopt-intermediate-inventory-conflict")
            if st["phase"] not in {"adopt-intent", "original-backed-up"}:
                raise PendingError("adopt-phase-physical-conflict")
            os.rename(candidate, src); _fsync_dir(candidate.parent); _fsync_dir(src.parent)
            st["phase"] = "candidate-promoted"; _write_state(job, st)
            st["phase"] = "adopted"; _write_state(job, st)
            states = (True, False, True)
        if states == (True, False, True):
            if st["phase"] not in {"original-backed-up", "candidate-promoted", "adopted"}:
                raise PendingError("adopt-phase-physical-conflict")
            if _inventory_sha(_inventory(src)) != st["candidate_sha256"] or _inventory_sha(_inventory(backup)) != st["source_sha256"]:
                raise PendingError("completed-operation-mismatch")
            if st["phase"] != "adopted":
                st["phase"] = "adopted"; _write_state(job, st)
            return 0
        raise PendingError("adopt-physical-conflict")

def _cmd_restore(args):
    job = _absolute(args.job, "job", exists=True, directory=True); st = _load_state(job)
    if st["phase"] not in {"adopted", "restore-intent", "adopted-backed-up", "restored"}:
        raise PendingError("restore-requires-adopted")
    src, backup = Path(st["source"]), Path(st["adopted_backup"])
    checkpoint = Path(st["checkpoint"]); stage = Path(st["restore_stage"])
    with _parent_lock(src), _existing_context_locks(src, backup, st["original_backup"]):
        if st["phase"] == "restored": return _completed(job, st)
        _revalidate_authority(job, st)
        _validate_boundary(job, st, record=False)
        if Path(st["candidate"]).exists(): raise PendingError("restore-unexpected-candidate-carrier")
        if not any(ref["path"] == "receipts/admission.json" for ref in st["receipts"]):
            raise PendingError("restore-admission-missing")
        if not stage.exists() and src.exists() and _inventory_sha(_inventory(src)) == st["candidate_sha256"]:
            _copy_bytes(checkpoint, stage)
        # Exact checkpoint inventory can legitimately omit .context-lock. Never
        # invent a persistent lock in the restored source. Parent lock plus bound
        # observed quiescence remains required; hold every existing stage inode.
        with _existing_context_locks(stage):
            src_exists, stage_exists, backup_exists = src.exists(), stage.exists(), backup.exists()
            src_hash = _inventory_sha(_inventory(src)) if src_exists else None
            stage_hash = _inventory_sha(_inventory(stage)) if stage_exists else None
            backup_hash = _inventory_sha(_inventory(backup)) if backup_exists else None
            state = (src_exists, stage_exists, backup_exists)
            if state == (True, True, False) and src_hash == st["candidate_sha256"] and stage_hash == st["checkpoint_sha256"]:
                if st["phase"] not in {"adopted", "restore-intent"}:
                    raise PendingError("restore-physical-state-regressed")
                st["phase"] = "restore-intent"; st["operation"] = "restore"; _write_state(job, st)
                os.rename(src, backup); _fsync_dir(src.parent); _fsync_dir(backup.parent)
                st["phase"] = "adopted-backed-up"; _write_state(job, st)
                state = (False, True, True)
            if state == (False, True, True):
                if st["phase"] not in {"restore-intent", "adopted-backed-up"}:
                    raise PendingError("restore-phase-physical-conflict")
                if (_inventory_sha(_inventory(stage)) != st["checkpoint_sha256"]
                        or _inventory_sha(_inventory(backup)) != st["candidate_sha256"]):
                    raise PendingError("restore-intermediate-inventory-conflict")
                os.rename(stage, src); _fsync_dir(stage.parent); _fsync_dir(src.parent)
                st["phase"] = "restored"; _write_state(job, st)
                state = (True, False, True)
            if state == (True, False, True):
                if st["phase"] not in {"adopted-backed-up", "restored"}:
                    raise PendingError("restore-phase-physical-conflict")
                if _inventory_sha(_inventory(src)) != st["checkpoint_sha256"] or _inventory_sha(_inventory(backup)) != st["candidate_sha256"]:
                    raise PendingError("completed-restore-mismatch")
                if st["phase"] != "restored":
                    st["phase"] = "restored"; _write_state(job, st)
                return 0
            raise PendingError("restore-physical-conflict")

def main(argv=None):
    parser = argparse.ArgumentParser(prog="compact.py")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("diagnose"); d.add_argument("--workspace", required=True); d.add_argument("--target", required=True); d.add_argument("--context", required=True); d.add_argument("--output", required=True); d.set_defaults(run=_cmd_diagnose)
    p = sub.add_parser("prepare"); p.add_argument("--manifest", required=True); p.add_argument("--job", required=True); p.set_defaults(run=_cmd_prepare)
    for name, fn in (("verify", _cmd_verify), ("adopt", _cmd_adopt), ("restore", _cmd_restore)):
        q = sub.add_parser(name); q.add_argument("--job", required=True); q.set_defaults(run=fn)
    args = parser.parse_args(argv)
    try:
        if args.command in {"verify", "adopt", "restore"}:
            _absolute(args.job, "job", exists=True, directory=True)
            try:
                return args.run(args)
            except (MigrationError, OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
                raise PendingError("existing-operation-conflict:" + str(exc)) from exc
        return args.run(args)
    except PendingError as exc:
        print("compact:" + str(exc), file=sys.stderr)
        return 1
    except (MigrationError, OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print("compact:" + str(exc), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
