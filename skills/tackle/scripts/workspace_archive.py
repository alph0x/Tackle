"""Read-only lookup and explicitly scoped reversible archive operations.

This module intentionally exposes Python functions only.  It has no command
line entry point and never infers a repository root or an authorization.
"""

import errno
import fcntl
import hashlib
import json
import math
import posixpath
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from contextlib import ExitStack
from datetime import datetime


CATALOG_SCHEMA = "tackle-workspace-archive/1"
QUALIFICATION_SCHEMA = "tackle-archive-qualification/1"
SCOPE_SCHEMA = "tackle-archive-scope/1"
WRITERS_SCHEMA = "tackle-archive-writers/1"
TRANSACTION_SCHEMA = "tackle-archive-transaction/1"
ID_RE = re.compile(r"[a-z0-9][a-z0-9.-]*\Z")
HEX_RE = re.compile(r"[0-9a-f]{64}\Z")
RESERVED = {".", "..", ".archive", "archive-index.md", "catalog.json", "transaction.json"}
CARD_KEYS = {"title", "purpose", "accepted_result", "exclusions", "reusable_decisions",
             "closed_at", "delivery_state", "delivery_links", "verification_links"}
QUALIFICATION_KEYS = {"schema", "id", "source_revision", "sources", "tasks", "accepted_delivery",
                      "obligations_resolved", "effects_settled", "maintenance_settled", "references",
                      "reference_scope", "reviewer", "observed_at", "card"}
SCOPE_KEYS = {"schema", "repo", "ids", "operations", "authorization_source"}
WRITER_KEYS = {"schema", "repo", "ids", "source_revisions", "observer", "observed_at",
               "cooperating_locks", "remaining_limits", "source_refs"}
ENTRY_KEYS = {"id", "original", "archive", "state", "revision", "inventory", "qualification", "card"}
INVENTORY_KEYS = {"kind", "mode", "sha256", "link"}


def _fail(message):
    raise ValueError(message)


def _exact(value, keys, label):
    _closed(value)
    if type(value) is not dict or set(value) != set(keys):
        _fail("invalid-" + label)


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    try:
        _closed(value)
        return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                           allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise ValueError("invalid-json-value") from error


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate-json-key")
        result[key] = value
    return result


def _json(raw, label):
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda _: _fail("nonfinite-json"))
        _closed(value)
        return value
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("invalid-" + label) from error


def _real_root(repo):
    try:
        path = Path(repo)
    except (TypeError, ValueError) as error:
        raise ValueError("invalid-repo") from error
    if not path.is_absolute():
        _fail("repo-must-be-absolute")
    try:
        info = path.lstat()
    except OSError as error:
        raise ValueError("invalid-repo") from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        _fail("invalid-repo")
    return path.resolve(strict=True)


def _safe_rel(value):
    if type(value) is not str or not value or "\\" in value or value.startswith("/"):
        _fail("invalid-path")
    path = PurePosixPath(value)
    if path.as_posix() != value or any(part in ("", ".", "..") for part in value.split("/")):
        _fail("invalid-path")
    return path


def _safe_id(value, allow_unknown=False):
    if type(value) is not str or not value:
        _fail("invalid-id")
    if allow_unknown:
        if value in RESERVED or "/" in value or "\\" in value:
            _fail("invalid-id")
        return value
    if not ID_RE.fullmatch(value) or value in RESERVED:
        _fail("invalid-id")
    return value


def _inside(root, path):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _path(root, rel, *, must_exist=False):
    relative = _safe_rel(rel)
    candidate = root.joinpath(*relative.parts)
    try:
        resolved = candidate.resolve(strict=must_exist)
    except (OSError, RuntimeError) as error:
        raise ValueError("unsafe-path") from error
    if not _inside(root, resolved):
        _fail("path-escapes-repo")
    return candidate


def _hash_file(path):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as error:
        if isinstance(error, FileNotFoundError):
            raise
        raise ValueError("unsafe-file") from error
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            _fail("not-regular-file")
        chunks = []
        while True:
            part = os.read(fd, 1024 * 1024)
            if not part:
                break
            chunks.append(part)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _safe_symlink(root, path, rel):
    target = os.readlink(path)
    if os.path.isabs(target) or "\\" in target:
        _fail("unsafe-symlink")
    try:
        resolved = (path.parent / target).resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError("unsafe-symlink") from error
    if not _inside(root, resolved):
        _fail("unsafe-symlink")
    return target


def _inventory(root):
    root = Path(root)
    root_info = root.lstat()
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        _fail("unsafe-workspace-root")
    result = {}

    def walk(path, relative):
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISLNK(info.st_mode):
            row = {"kind": "symlink", "mode": mode, "sha256": None,
                   "link": _safe_symlink(root, path, relative)}
        elif stat.S_ISDIR(info.st_mode):
            row = {"kind": "directory", "mode": mode, "sha256": None, "link": None}
        elif stat.S_ISREG(info.st_mode):
            raw = _hash_file(path)
            row = {"kind": "file", "mode": mode, "sha256": _digest(raw), "link": None}
        else:
            _fail("unsupported-file-type")
        result[relative] = row
        if row["kind"] == "directory":
            with os.scandir(path) as entries:
                names = sorted(entry.name for entry in entries)
            for name in names:
                child_relative = name if relative == "." else relative + "/" + name
                _safe_rel(child_relative)
                walk(path / name, child_relative)

    walk(root, ".")
    return result


def _validate_inventory(value):
    _closed(value)
    if type(value) is not dict or "." not in value:
        _fail("invalid-inventory")
    for name, row in value.items():
        if name != ".":
            _safe_rel(name)
        _exact(row, INVENTORY_KEYS, "inventory-row")
        if type(row["mode"]) is not int or not 0 <= row["mode"] <= 0o7777:
            _fail("invalid-inventory-mode")
        if row["kind"] == "file":
            _hex(row["sha256"], "inventory-file")
            if row["link"] is not None:
                _fail("invalid-inventory-file")
        elif row["kind"] == "symlink":
            if type(row["link"]) is not str or not row["link"] or os.path.isabs(row["link"]) or "\\" in row["link"] or row["sha256"] is not None:
                _fail("invalid-inventory-link")
        elif row["kind"] == "directory":
            if row["sha256"] is not None or row["link"] is not None:
                _fail("invalid-inventory-directory")
        else:
            _fail("invalid-inventory-kind")
    if value["."]["kind"] != "directory":
        _fail("invalid-inventory-root")
    for name in value:
        if name != ".":
            parent = str(PurePosixPath(name).parent)
            if parent not in value or value[parent]["kind"] != "directory":
                _fail("invalid-inventory-parent")


def _revision(inventory):
    _validate_inventory(inventory)
    return _digest(_canonical(inventory))


def _reference(root, value):
    _exact(value, {"path", "sha256"}, "reference")
    if not isinstance(value["sha256"], str) or not HEX_RE.fullmatch(value["sha256"]):
        _fail("invalid-reference-hash")
    path = _path(root, value["path"], must_exist=True)
    if path.is_symlink() or not path.is_file():
        _fail("reference-not-file")
    try:
        raw = _hash_file(path)
    except FileNotFoundError as error:
        raise ValueError("reference-missing") from error
    if _digest(raw) != value["sha256"]:
        _fail("reference-drift")
    return path, raw


def _timestamp(value):
    if type(value) is not str:
        _fail("invalid-observed-at")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid-observed-at") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail("invalid-observed-at")


def _card(card):
    _exact(card, CARD_KEYS, "card")
    for key in ("title", "purpose", "accepted_result"):
        if type(card[key]) is not str or not card[key].strip():
            _fail("invalid-card-text")
    for key in ("exclusions", "reusable_decisions"):
        if type(card[key]) is not list or any(type(item) is not str for item in card[key]):
            _fail("invalid-card-list")
    if card["closed_at"] is not None:
        _timestamp(card["closed_at"])
    if card["delivery_state"] not in ("released", "pending", "unknown"):
        _fail("invalid-delivery-state")
    for key in ("delivery_links", "verification_links"):
        if type(card[key]) is not list:
            _fail("invalid-card-links")
        for link in card[key]:
            _exact(link, {"label", "path", "sha256"}, "card-link")
            if type(link["label"]) is not str or not link["label"]:
                _fail("invalid-card-link-label")
            _safe_rel(link["path"])
            if not isinstance(link["sha256"], str) or not HEX_RE.fullmatch(link["sha256"]):
                _fail("invalid-card-link-hash")


def _workspace_paths(root, id):
    _validate_plans_root(root)
    plans = root / "docs/plans"
    return plans / id, plans / ".archive" / id


def _validate_plans_root(root):
    for path in (root / "docs", root / "docs/plans"):
        try:
            info = path.lstat()
        except FileNotFoundError as error:
            raise ValueError("plans-root-missing") from error
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            _fail("unsafe-plans-root")


def _metadata_paths(root):
    _validate_plans_root(root)
    return root / "docs/plans/.archive", root / "docs/plans/.archive/catalog.json", root / "docs/plans/archive-index.md"


def _validate_catalog(value):
    _exact(value, {"schema", "entries"}, "catalog")
    if value["schema"] != CATALOG_SCHEMA or type(value["entries"]) is not dict:
        _fail("invalid-catalog")
    for id, entry in value["entries"].items():
        _safe_id(id)
        _exact(entry, ENTRY_KEYS, "catalog-entry")
        if entry["id"] != id or entry["state"] not in ("active", "archived"):
            _fail("invalid-catalog-entry")
        for key in ("original", "archive"):
            path = _safe_rel(entry[key]).as_posix()
            expected = "docs/plans/" + id if key == "original" else "docs/plans/.archive/" + id
            if path != expected:
                _fail("invalid-catalog-path")
        _validate_inventory(entry["inventory"])
        if entry["revision"] != _revision(entry["inventory"]):
            _fail("invalid-catalog-revision")
        _card(entry["card"])
        if type(entry["qualification"]) is not str or not HEX_RE.fullmatch(entry["qualification"]):
            _fail("invalid-catalog-qualification")


def _escape(text):
    text = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\n", " ").replace("\r", " ")
    return "".join("\\" + char if char in "\\`*_{}[]()#+-.!|" else char for char in text)


def _render_index(catalog):
    lines = ["# Archived workspaces", "", "This is a projection of the archive catalog; task state remains in each original workspace.", ""]
    for id, entry in sorted(catalog["entries"].items()):
        if entry["state"] != "archived":
            continue
        card = entry["card"]
        lines.extend(("## " + _escape(card["title"]),
                      "- ID: `" + id + "`",
                      "- Purpose: " + _escape(card["purpose"]),
                      "- Accepted result: " + _escape(card["accepted_result"]),
                      "- Closed: " + (_escape(card["closed_at"]) if card["closed_at"] else "unknown"),
                      "- Delivery: " + _escape(card["delivery_state"])))
        for exclusion in card["exclusions"]:
            lines.append("- Excluded: " + _escape(exclusion))
        for decision in card["reusable_decisions"]:
            lines.append("- Decision: " + _escape(decision))
        for key, label in (("delivery_links", "Delivery link"), ("verification_links", "Verification link")):
            for link in card[key]:
                lines.append("- " + label + ": [" + _escape(link["label"]) + "](" +
                             _link_destination(catalog, link["path"]) + ")")
        lines.append("- Archive: [" + _escape(id) + "](" + _link_destination(catalog, entry["archive"]) + "/)")
        lines.append("")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _read_catalog(root, *, required=False):
    archive, catalog_path, index_path = _metadata_paths(root)
    if archive.is_symlink():
        _fail("unsafe-archive-root")
    catalog_exists = catalog_path.exists() or catalog_path.is_symlink()
    index_exists = index_path.exists() or index_path.is_symlink()
    if not catalog_exists and not index_exists:
        if required:
            _fail("metadata-conflict")
        return {"schema": CATALOG_SCHEMA, "entries": {}}, None, None
    if not catalog_exists or not index_exists or catalog_path.is_symlink() or index_path.is_symlink():
        _fail("metadata-conflict")
    catalog_raw = _hash_file(catalog_path)
    catalog = _json(catalog_raw, "catalog")
    _validate_catalog(catalog)
    index_raw = _hash_file(index_path)
    if index_raw != _render_index(catalog):
        _fail("metadata-conflict")
    return catalog, _digest(catalog_raw), _digest(index_raw)


def _check_tree(root, path, expected):
    if not path.exists() or path.is_symlink():
        return False
    try:
        return _inventory(path) == expected
    except (OSError, ValueError):
        return False


def _read_transaction(root):
    archive, _, _ = _metadata_paths(root)
    if archive.is_symlink():
        _fail("unsafe-archive-root")
    journal = archive / "transaction.json"
    if journal.is_symlink():
        _fail("metadata-conflict")
    if not journal.exists():
        return None
    if not journal.is_file():
        _fail("metadata-conflict")
    tx = _json(_hash_file(journal), "transaction")
    _exact(tx, {"schema", "operation", "id", "origin", "destination", "source_revision", "inventory",
                "old_catalog_sha256", "old_index_sha256", "next_catalog", "next_index", "scope_sha256",
                "writer_receipt_sha256"}, "transaction")
    if tx["schema"] != TRANSACTION_SCHEMA or tx["operation"] not in ("archive", "restore"):
        _fail("metadata-conflict")
    _safe_id(tx["id"])
    _validate_inventory(tx["inventory"])
    if tx["source_revision"] != _revision(tx["inventory"]):
        _fail("metadata-conflict")
    _validate_catalog(tx["next_catalog"])
    if type(tx["next_index"]) is not str or tx["next_index"].encode("utf-8") != _render_index(tx["next_catalog"]):
        _fail("metadata-conflict")
    for key in ("scope_sha256", "writer_receipt_sha256"):
        _hex(tx[key], "transaction")
    for key in ("old_catalog_sha256", "old_index_sha256"):
        if tx[key] is not None:
            _hex(tx[key], "transaction")
    if (tx["old_catalog_sha256"] is None) != (tx["old_index_sha256"] is None):
        _fail("metadata-conflict")
    expected_origin, expected_destination = _workspace_paths(root, tx["id"])
    if tx["operation"] == "restore":
        expected_origin, expected_destination = expected_destination, expected_origin
    if type(tx["origin"]) is not str or type(tx["destination"]) is not str or tx["origin"] != str(expected_origin) or tx["destination"] != str(expected_destination):
        _fail("metadata-conflict")
    entry = tx["next_catalog"]["entries"].get(tx["id"])
    if entry is None or entry["inventory"] != tx["inventory"] or entry["revision"] != tx["source_revision"] or entry["state"] != ("archived" if tx["operation"] == "archive" else "active"):
        _fail("metadata-conflict")
    return tx


def _pending(root):
    tx = _read_transaction(root)
    if tx is None:
        return []
    return [{"id": tx["id"], "direction": tx["operation"]}]


def _refuse_pending_writer(root):
    archive = _metadata_paths(root)[0]
    if archive.is_symlink():
        _fail("unsafe-archive-root")
    journal = archive / "transaction.json"
    if not journal.exists() and not journal.is_symlink():
        return
    # Probe only an existing lock before parsing a possibly live journal.
    lock = archive / ".maintenance-lock"
    fd = None
    try:
        if lock.exists() or lock.is_symlink():
            if lock.is_symlink() or not lock.is_file():
                _fail("unsafe-archive-lock")
            fd = os.open(lock, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                _fail("unsafe-archive-lock")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("writer-active") from error
        if _pending(root):
            _fail("pending-transaction")
    finally:
        if fd is not None:
            os.close(fd)


def _closed(value, active=None):
    """Accept builtin finite JSON values only, without coercion or cycles."""
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ValueError("invalid-json-string") from error
        return
    if value is None or type(value) in (bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            _fail("nonfinite-json")
        return
    if type(value) not in (dict, list):
        _fail("invalid-json-type")
    active = set() if active is None else active
    identity = id(value)
    if identity in active:
        _fail("cyclic-json")
    active.add(identity)
    try:
        if type(value) is dict:
            if any(type(key) is not str for key in value):
                _fail("invalid-json-key")
            for key in value:
                _closed(key, active)
            children = value.values()
        else:
            children = value
        for child in children:
            _closed(child, active)
    except RecursionError as error:
        raise ValueError("invalid-json-depth") from error
    finally:
        active.remove(identity)


def _hex(value, label):
    if type(value) is not str or not HEX_RE.fullmatch(value):
        _fail("invalid-" + label + "-hash")
    return value


def _link_destination(catalog, path):
    original = _safe_rel(path).as_posix()
    current = original
    for entry in sorted(catalog["entries"].values(), key=lambda row: len(row["original"]), reverse=True):
        prefix = entry["original"]
        if original == prefix or original.startswith(prefix + "/"):
            current = (entry["archive"] if entry["state"] == "archived" else prefix) + original[len(prefix):]
            break
    local = posixpath.relpath(current, "docs/plans")
    safe = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~/"
    return "".join(chr(byte) if byte in safe else "%{:02X}".format(byte) for byte in local.encode("utf-8"))


def _settled_inventory(inventory):
    for name in inventory:
        parts = name.split("/")
        if name == "history/transaction.md":
            _fail("context-maintenance-pending")
        if name in ("verification-records/.lock", "verification-records/store/.lock"):
            _fail("record-store-lease-active")
        if parts[0] == "verification-records" and inventory[name]["kind"] == "directory" and parts[-1].startswith(".pending-"):
            _fail("record-capture-pending")


def _unfenced(text):
    lines, fence = [], None
    for line in text.splitlines():
        mark = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if mark and mark[1][0] == fence[0] and len(mark[1]) >= fence[1] and not mark[2].strip():
                fence = None
            continue
        if mark:
            fence = (mark[1][0], len(mark[1]))
        else:
            lines.append(line)
    if fence:
        _fail("unclosed-board-fence")
    return lines


def _board_tasks(source):
    boards = [source / name for name in ("board.md", "task-board.md")
              if (source / name).exists() or (source / name).is_symlink()]
    if len(boards) > 1:
        _fail("ambiguous-task-board")
    plan = source / "plan.md"
    lite = plan.is_file() and not plan.is_symlink() and _hash_file(plan).splitlines()[:1] == [b"Gate: Lite"]
    if lite:
        if boards:
            _fail("ambiguous-lite-board")
        # Lite has no canonical task table; its actual declared task set is reviewed.
        return None
    if not boards:
        _fail("missing-task-board")
    board = boards[0]
    try:
        lines = _unfenced(_hash_file(board).decode("utf-8"))
    except UnicodeDecodeError as error:
        raise ValueError("invalid-task-board-encoding") from error
    schemas = [line[len("Schema:"):].strip() for line in lines if line.startswith("Schema:")]
    if len(schemas) > 1:
        _fail("ambiguous-task-board-schema")
    schema = schemas[0] if schemas else None
    if board.name == "board.md":
        if schema not in (None, "tackle-workspace/3"):
            _fail("unknown-task-board-schema")
        pre3 = schema is None
    else:
        if schema not in ("tackle-workspace/4", "tackle-workspace/5"):
            _fail("unknown-task-board-schema")
        pre3 = False
    split = lambda line: [cell.strip() for cell in line.strip().strip("|").split("|")]
    tables = []
    for index, line in enumerate(lines[:-1]):
        if not line.strip().startswith("|") or not re.fullmatch(r"\|?[\s:|-]+\|?", lines[index + 1].strip()) or "-" not in lines[index + 1]:
            continue
        header = split(line)
        if "Status" in header and any(name in header for name in ("Task", "Point")):
            tables.append((index, header))
    if len(tables) != 1:
        _fail("ambiguous-or-missing-task-table")
    index, header = tables[0]
    if len(set(header)) != len(header) or sum(name in header for name in ("Task", "Point")) != 1:
        _fail("invalid-task-header")
    if pre3:
        groups = (("Task", "Point"), ("What",), ("Brief", "Briefing"), ("Depends on",),
                  ("Status",), ("Confidence", "Verification"))
        if any(sum(name in header for name in group) != 1 for group in groups) or len(header) != len(groups):
            _fail("unrecognized-pre3-header")
    elif "Task" not in header:
        _fail("invalid-task-header")
    id_column = header.index("Task" if "Task" in header else "Point")
    status_column = header.index("Status")
    glyphs = {"\U0001F534": "Draft", "\U0001F7E1": "In progress", "⏸": "Blocked", "\U0001F7E2": "Complete", "⚪": "Skipped"}
    states = {"Draft", "Ready to run", "In progress", "Checking", "Complete", "Blocked", "Interrupted", "Skipped", "Unverifiable", "Waiting on owner"}
    rows = {}
    for line in lines[index + 2:]:
        if not line.strip().startswith("|"):
            break
        cells = split(line)
        if len(cells) != len(header):
            _fail("invalid-task-row")
        identity = cells[id_column]
        if not re.fullmatch(r"[PT]-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", identity):
            _fail("invalid-task-identity")
        if identity in rows:
            _fail("duplicate-task")
        status = cells[status_column]
        if status not in states:
            legacy = re.fullmatch(r"(.?)\ufe0f?\s*(.*)", status, re.S)
            if not legacy or legacy[1] not in glyphs:
                _fail("unknown-task-status")
            status = glyphs[legacy[1]]
        rows[identity] = status
    if not rows:
        _fail("missing-task-rows")
    return rows


def _cited_input(root, relative, expected_hash):
    _hex(expected_hash, "reference")
    path = _path(root, relative, must_exist=True)
    if path.is_symlink():
        _fail("reference-not-file-or-root")
    if path.is_dir():
        observed = _revision(_inventory(path))
    elif path.is_file():
        observed = _digest(_hash_file(path))
    else:
        _fail("reference-not-file-or-root")
    if observed != expected_hash:
        _fail("reference-drift")


def _member_file(base, relative, expected):
    """Verify only the selected path/alias chain and its regular final target."""
    root_info = base.lstat()
    if not stat.S_ISDIR(root_info.st_mode) or stat.S_ISLNK(root_info.st_mode):
        _fail("unsafe-workspace-root")
    if expected is not None and stat.S_IMODE(root_info.st_mode) != expected["."]["mode"]:
        _fail("member-drift")
    try:
        resolved = (base / relative).resolve(strict=True)
    except (RuntimeError, OSError) as error:
        # A symlink loop is RuntimeError before Python 3.13 and OSError(ELOOP) from 3.13 on.
        if isinstance(error, OSError) and error.errno != errno.ELOOP:
            raise
        raise ValueError("member-link-conflict") from error
    if not _inside(base.resolve(strict=True), resolved):
        _fail("member-escapes-workspace")
    pending, parts = relative.split("/"), []
    while pending:
        part = pending.pop(0)
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                _fail("member-escapes-workspace")
            parts.pop()
            continue
        key = "/".join(parts + [part])
        path = base.joinpath(*(parts + [part]))
        info = path.lstat()
        kind = "symlink" if stat.S_ISLNK(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "file" if stat.S_ISREG(info.st_mode) else None
        row = expected.get(key) if expected is not None else None
        if kind is None or (expected is not None and (row is None or row["kind"] != kind or row["mode"] != stat.S_IMODE(info.st_mode))):
            _fail("member-drift")
        if kind == "symlink":
            target = os.readlink(path)
            if os.path.isabs(target) or "\\" in target or not target or (row is not None and row["link"] != target):
                _fail("member-drift")
            pending = target.split("/") + pending
        elif kind == "directory":
            parts.append(part)
        else:
            if pending:
                _fail("invalid-member")
            raw = _hash_file(path)
            if row is not None and _digest(raw) != row["sha256"]:
                _fail("member-drift")
            return raw
    _fail("invalid-member")


def _qualify(root, source, id, qualification):
    _exact(qualification, QUALIFICATION_KEYS, "qualification")
    if qualification["schema"] != QUALIFICATION_SCHEMA or qualification["id"] != id:
        _fail("invalid-qualification")
    if type(qualification["source_revision"]) is not str or not HEX_RE.fullmatch(qualification["source_revision"]):
        _fail("invalid-qualification-revision")
    observed_inventory = _inventory(source)
    revision = _revision(observed_inventory)
    if qualification["source_revision"] != revision:
        _fail("stale-qualification")
    _settled_inventory(observed_inventory)
    for flag in ("accepted_delivery", "obligations_resolved", "effects_settled", "maintenance_settled"):
        if qualification[flag] is not True:
            _fail("qualification-incomplete-" + flag)
    if type(qualification["reviewer"]) is not str or not qualification["reviewer"].strip():
        _fail("invalid-reviewer")
    _timestamp(qualification["observed_at"])
    _card(qualification["card"])
    for key in ("delivery_links", "verification_links"):
        for link in qualification["card"][key]:
            _reference(root, {"path": link["path"], "sha256": link["sha256"]})
    source_refs = {}
    seen_sources = set()
    if type(qualification["sources"]) is not list or not qualification["sources"]:
        _fail("invalid-qualification-sources")
    for row in qualification["sources"]:
        _exact(row, {"path", "sha256", "claim"}, "qualification-source")
        if row["claim"] not in ("closure", "obligations", "effects", "maintenance", "references"):
            _fail("invalid-qualification-claim")
        _safe_rel(row["path"])
        _hex(row["sha256"], "qualification-source")
        identity = (row["claim"], row["path"], row["sha256"])
        if identity in seen_sources:
            _fail("duplicate-qualification-source")
        seen_sources.add(identity)
        path, raw = _reference(root, {"path": row["path"], "sha256": row["sha256"]})
        source_refs[row["claim"]] = (path, raw)
    if set(source_refs) != {"closure", "obligations", "effects", "maintenance", "references"}:
        _fail("qualification-claims-incomplete")
    # The cited bytes are inspected semantically by the qualification reviewer.
    # Structural consistency and source stability do not infer truth from prose.
    tasks = qualification["tasks"]
    if type(tasks) is not list:
        _fail("invalid-qualification-tasks")
    task_ids = set()
    for task in tasks:
        _exact(task, {"id", "state", "receipt", "disposition"}, "qualification-task")
        if type(task["id"]) is not str or task["id"] in task_ids:
            _fail("duplicate-task")
        task_ids.add(task["id"])
        if task["state"] not in ("Complete", "Skipped", "Unverifiable"):
            _fail("task-not-closed")
        if task["disposition"] not in ("accepted", "accepted-exclusion", "accepted-withdrawal"):
            _fail("task-not-accepted")
        _reference(root, task["receipt"])
        if task["state"] == "Complete" and task["disposition"] != "accepted":
            _fail("complete-task-not-accepted")
        if task["state"] == "Skipped" and task["disposition"] != "accepted-exclusion":
            _fail("skipped-task-not-excluded")
        if task["state"] == "Unverifiable":
            if task["disposition"] != "accepted-withdrawal":
                _fail("unverifiable-obligation-open")
    rows = _board_tasks(source)
    if rows is not None:
        if set(rows) != task_ids:
            _fail("task-set-mismatch")
        for task in tasks:
            if rows.get(task["id"]) != task["state"]:
                _fail("task-state-mismatch")
    references = qualification["references"]
    if type(references) is not list:
        _fail("invalid-references")
    for reference in references:
        _exact(reference, {"consumer", "path", "sha256", "required", "mode", "disposition", "evidence"}, "reference-row")
        if type(reference["consumer"]) is not str or type(reference["required"]) is not bool:
            _fail("invalid-reference-row")
        if reference["mode"] not in ("logical", "direct", "historical-data") or reference["disposition"] not in ("preserved", "refused", "unknown"):
            _fail("invalid-reference-row")
        _safe_rel(reference["path"])
        _hex(reference["sha256"], "reference-row")
        if type(reference["evidence"]) is not list:
            _fail("invalid-reference-evidence")
        for evidence in reference["evidence"]:
            _reference(root, evidence)
        if reference["mode"] != "historical-data":
            _cited_input(root, reference["path"], reference["sha256"])
            if reference["required"] and reference["disposition"] != "preserved":
                _fail("required-reference-unresolved")
    reference_scope = qualification["reference_scope"]
    _exact(reference_scope, {"inputs", "diagnostic"}, "reference-scope")
    if type(reference_scope["inputs"]) is not list or not reference_scope["inputs"] or type(reference_scope["diagnostic"]) is not str or not reference_scope["diagnostic"].strip():
        _fail("invalid-reference-scope")
    for datum in reference_scope["inputs"]:
        _reference(root, datum)
    return observed_inventory, revision


def _scope(root, id, scope, operation):
    if scope is None:
        raise PermissionError("scope-required")
    _exact(scope, SCOPE_KEYS, "scope")
    if scope["schema"] != SCOPE_SCHEMA or scope["repo"] != str(root):
        raise PermissionError("scope-mismatch")
    if type(scope["ids"]) is not list or any(type(item) is not str for item in scope["ids"]):
        raise PermissionError("scope-id-mismatch")
    if id not in scope["ids"] or len(scope["ids"]) != len(set(scope["ids"])):
        raise PermissionError("scope-id-mismatch")
    if type(scope["operations"]) is not list or any(type(item) is not str for item in scope["operations"]):
        raise PermissionError("scope-operation-invalid")
    if operation not in scope["operations"] or len(set(scope["operations"])) != len(scope["operations"]):
        raise PermissionError("scope-operation-missing")
    for item in scope["ids"]:
        _safe_id(item)
    if any(item not in ("archive", "recover", "restore") for item in scope["operations"]):
        raise PermissionError("scope-operation-invalid")
    _reference(root, scope["authorization_source"])
    return _digest(_canonical(scope))


def _writer(root, id, revision, scope_hash, writer_receipt, operation):
    if writer_receipt is None:
        raise PermissionError("writer-receipt-required")
    _exact(writer_receipt, WRITER_KEYS, "writer-receipt")
    if writer_receipt["schema"] != WRITERS_SCHEMA or writer_receipt["repo"] != str(root):
        raise PermissionError("writer-receipt-mismatch")
    ids = writer_receipt["ids"]
    if type(ids) is not list or any(type(item) is not str for item in ids) or id not in ids or len(set(ids)) != len(ids):
        raise PermissionError("writer-id-mismatch")
    for item in ids:
        _safe_id(item)
    revisions = writer_receipt["source_revisions"]
    if type(revisions) is not dict or set(revisions) != set(ids) or revisions[id] != revision:
        _fail("writer-revision-mismatch")
    for value in revisions.values():
        _hex(value, "writer-revision")
    if type(writer_receipt["observer"]) is not str or not writer_receipt["observer"].strip():
        _fail("invalid-writer-observer")
    _timestamp(writer_receipt["observed_at"])
    if type(writer_receipt["remaining_limits"]) is not list or any(type(item) is not str for item in writer_receipt["remaining_limits"]):
        _fail("invalid-writer-limits")
    if type(writer_receipt["cooperating_locks"]) is not list or type(writer_receipt["source_refs"]) is not list or not writer_receipt["source_refs"]:
        _fail("invalid-writer-receipt")
    refs = []
    for ref in writer_receipt["source_refs"]:
        _reference(root, ref)
        identity = (ref["path"], ref["sha256"])
        if identity in refs:
            _fail("duplicate-writer-source")
        refs.append(identity)
    journal_path = _metadata_paths(root)[0] / "transaction.json"
    if journal_path.exists() and (journal_path.relative_to(root).as_posix(), _digest(_hash_file(journal_path))) not in refs:
        _fail("writer-receipt-journal-unpinned")
    active, archived = _workspace_paths(root, id)
    carrier = archived if archived.exists() else active
    lock = carrier / ".context-lock"
    expected = []
    if lock.exists() or lock.is_symlink():
        if lock.is_symlink() or not lock.is_file():
            _fail("writer-lock-unsafe")
        expected.append({"path": lock.relative_to(root).as_posix(), "protocol": "flock"})
    for lock_row in writer_receipt["cooperating_locks"]:
        _exact(lock_row, {"path", "protocol"}, "writer-lock")
        _safe_rel(lock_row["path"])
        if lock_row["protocol"] != "flock":
            _fail("invalid-writer-lock-protocol")
    if writer_receipt["cooperating_locks"] != expected:
        _fail("writer-lock-observation-mismatch")
    _hex(scope_hash, "scope")
    return _digest(_canonical(writer_receipt))


def _locked(root, carrier):
    stack = ExitStack()
    try:
        # Lock the already-existing workspace carrier before creating archive metadata.
        # A busy cooperating writer therefore causes no archive-side effect.
        lock_path = carrier / ".context-lock"
        if lock_path.exists() or lock_path.is_symlink():
            if lock_path.is_symlink() or not lock_path.is_file():
                _fail("writer-lock-unsafe")
            source_fd = os.open(lock_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            source_info = os.fstat(source_fd)
            if not stat.S_ISREG(source_info.st_mode):
                os.close(source_fd)
                _fail("writer-lock-unsafe")
            try:
                fcntl.flock(source_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                os.close(source_fd)
                raise ValueError("writer-active") from error
            stack.callback(_unlock_close, source_fd)
        archive = _metadata_paths(root)[0]
        if archive.exists() and archive.is_symlink():
            _fail("unsafe-archive-root")
        if not archive.exists():
            archive.mkdir()
            _fsync_dir(archive.parent)
        if not archive.is_dir():
            _fail("unsafe-archive-root")
        archive_lock = archive / ".maintenance-lock"
        if archive_lock.is_symlink():
            _fail("unsafe-archive-lock")
        fd = os.open(archive_lock, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            os.close(fd)
            _fail("unsafe-archive-lock")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            os.close(fd)
            raise ValueError("writer-active") from error
        stack.callback(_unlock_close, fd)
        return stack
    except BaseException:
        stack.close()
        raise


def _unlock_close(fd):
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def _fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _require_same_filesystem(left_parent, right_parent):
    left = left_parent.stat()
    right = right_parent.stat()
    if not stat.S_ISDIR(left.st_mode) or not stat.S_ISDIR(right.st_mode):
        _fail("unsafe-rename-parent")
    if left.st_dev != right.st_dev:
        _fail("cross-device-move")


def _atomic(path, raw):
    fd, temp_name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        _fsync_dir(path.parent)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def _metadata_state(root):
    archive, catalog_path, index_path = _metadata_paths(root)
    if archive.is_symlink():
        _fail("unsafe-archive-root")
    catalog_exists = catalog_path.exists()
    index_exists = index_path.exists()
    if catalog_exists != index_exists:
        _fail("metadata-conflict")
    if not catalog_exists:
        return {"schema": CATALOG_SCHEMA, "entries": {}}, None, None
    catalog_raw = _hash_file(catalog_path)
    catalog = _json(catalog_raw, "catalog")
    _validate_catalog(catalog)
    index_raw = _hash_file(index_path)
    if index_raw != _render_index(catalog):
        _fail("metadata-conflict")
    return catalog, _digest(catalog_raw), _digest(index_raw)


def _write_journal(root, tx):
    journal = _metadata_paths(root)[0] / "transaction.json"
    if journal.exists() or journal.is_symlink():
        _fail("pending-transaction")
    raw = _canonical(tx)
    fd = os.open(journal, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                _fail("journal-write-failed")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_dir(journal.parent)


def _revalidate_authority(root, id, revision, scope, writer_receipt, operation, scope_hash, writer_hash):
    if _scope(root, id, scope, operation) != scope_hash:
        _fail("scope-drift")
    if _writer(root, id, revision, scope_hash, writer_receipt, operation) != writer_hash:
        _fail("writer-receipt-drift")


def _verify_published(root, tx):
    _, cat_sha, index_sha = _read_catalog(root, required=True)
    if cat_sha != _digest(_canonical(tx["next_catalog"])) or index_sha != _digest(tx["next_index"].encode("utf-8")):
        _fail("metadata-conflict")
    if _read_transaction(root) != tx:
        _fail("transaction-drift")


def _publish_next(root, tx):
    archive, catalog_path, index_path = _metadata_paths(root)
    _atomic(catalog_path, _canonical(tx["next_catalog"]))
    _atomic(index_path, tx["next_index"].encode("utf-8"))


def _remove_journal(root):
    journal = _metadata_paths(root)[0] / "transaction.json"
    journal.unlink()
    _fsync_dir(journal.parent)


def _result(id, state, path, revision, status):
    return {"id": id, "state": state, "path": str(path) if path is not None else None,
            "revision": revision, "status": status}


def _transaction(root, operation, id, origin, destination, revision, inventory, old_catalog_sha,
                 old_index_sha, next_catalog, scope_hash, writer_hash):
    index_text = _render_index(next_catalog).decode("utf-8")
    return {"schema": TRANSACTION_SCHEMA, "operation": operation, "id": id,
            "origin": str(origin), "destination": str(destination), "source_revision": revision,
            "inventory": inventory, "old_catalog_sha256": old_catalog_sha,
            "old_index_sha256": old_index_sha, "next_catalog": next_catalog,
            "next_index": index_text, "scope_sha256": scope_hash,
            "writer_receipt_sha256": writer_hash}


def _catalog_entry(id, original, archive, revision, inventory, qualification_hash, card, state):
    return {"id": id, "original": original.relative_to(original.parents[1]).as_posix(),
            "archive": archive.relative_to(archive.parents[2]).as_posix(), "state": state,
            "revision": revision, "inventory": inventory,
            "qualification": qualification_hash, "card": card}


def _expected_archive_rel(id):
    return "docs/plans/.archive/" + id


def _expected_original_rel(id):
    return "docs/plans/" + id


def _metadata_file_state(root, tx):
    archive, catalog_path, index_path = _metadata_paths(root)
    catalog_raw = _hash_file(catalog_path) if catalog_path.exists() else None
    index_raw = _hash_file(index_path) if index_path.exists() else None
    old_catalog = tx["old_catalog_sha256"]
    old_index = tx["old_index_sha256"]
    next_catalog_raw = _canonical(tx["next_catalog"])
    next_index_raw = tx["next_index"].encode("utf-8")
    cat_actual = _digest(catalog_raw) if catalog_raw is not None else None
    index_actual = _digest(index_raw) if index_raw is not None else None
    states = ((old_catalog, old_index),
              (_digest(next_catalog_raw), old_index),
              (_digest(next_catalog_raw), _digest(next_index_raw)))
    if (cat_actual, index_actual) not in states:
        _fail("metadata-conflict")
    if cat_actual == old_catalog:
        old = {"schema": CATALOG_SCHEMA, "entries": {}} if catalog_raw is None else _json(catalog_raw, "catalog")
        _validate_catalog(old)
        previous = old["entries"].get(tx["id"])
        next_entry = tx["next_catalog"]["entries"][tx["id"]]
        if tx["operation"] == "archive":
            if previous is not None:
                _fail("metadata-conflict")
        elif previous is None or previous["state"] != "archived" or dict(previous, state="active") != next_entry:
            _fail("metadata-conflict")
        expected_entries = dict(old["entries"])
        expected_entries[tx["id"]] = next_entry
        if expected_entries != tx["next_catalog"]["entries"]:
            _fail("metadata-conflict")
    catalog_next = cat_actual == _digest(next_catalog_raw)
    index_next = index_actual == _digest(next_index_raw)
    if index_next and not catalog_next:
        _fail("metadata-conflict")
    return catalog_next, index_next


def _finish_transaction(root, tx):
    id = tx["id"]
    origin, destination = Path(tx["origin"]), Path(tx["destination"])
    origin_exists = origin.exists() and not origin.is_symlink()
    dest_exists = destination.exists() and not destination.is_symlink()
    if origin_exists == dest_exists:
        _fail("location-conflict")
    tree = origin if origin_exists else destination
    if not _check_tree(root, tree, tx["inventory"]):
        _fail("inventory-conflict")
    catalog_next, index_next = _metadata_file_state(root, tx)
    if origin_exists:
        if catalog_next or index_next:
            _fail("metadata-conflict")
        if destination.exists() or destination.is_symlink():
            _fail("occupied-destination")
        _require_same_filesystem(origin.parent, destination.parent)
        os.rename(origin, destination)
        _fsync_dir(origin.parent)
        _fsync_dir(destination.parent)
    archive, catalog_path, index_path = _metadata_paths(root)
    if not catalog_next:
        _atomic(catalog_path, _canonical(tx["next_catalog"]))
    if not index_next:
        _atomic(index_path, tx["next_index"].encode("utf-8"))
    if not _check_tree(root, destination, tx["inventory"]):
        _fail("inventory-conflict")
    _verify_published(root, tx)
    _remove_journal(root)
    state = "archived" if tx["operation"] == "archive" else "active"
    final_path = destination
    return _result(id, state, final_path, tx["source_revision"], "recovered")


def list_workspaces(repo, state="active", query=None):
    """Return active, archived or combined workspace entries without mutation."""
    root = _real_root(repo)
    if state not in ("active", "archived", "all"):
        _fail("invalid-state")
    if query is not None and type(query) is not str:
        _fail("invalid-query")
    pending = _pending(root)
    if pending:
        return {"entries": [], "pending": pending,
                "diagnostics": [{"id": row["id"], "code": "pending-transaction"} for row in pending]}
    catalog, _, _ = _read_catalog(root)
    plans = root / "docs/plans"
    diagnostics, entries = [], []
    needle = query.casefold() if query is not None else None
    if state in ("active", "all"):
        for child in sorted(plans.iterdir(), key=lambda path: path.name):
            recorded = catalog["entries"].get(child.name)
            if child.name in (".archive", "archive-index.md"):
                continue
            if recorded and recorded["state"] == "archived":
                diagnostics.append({"id": child.name, "code": "active-archive-location-conflict"})
                continue
            try:
                if not child.is_dir() or child.is_symlink():
                    continue
                row = {"id": child.name, "path": str(child.resolve()), "state": "active", "card": None}
                if not ID_RE.fullmatch(child.name) or child.name in RESERVED:
                    diagnostics.append({"id": child.name, "code": "unqualified-active-name"})
                if needle is None or needle in child.name.casefold():
                    entries.append(row)
                    continue
                plan = child / "plan.md"
                if not plan.is_file() or plan.is_symlink():
                    diagnostics.append({"id": child.name, "code": "active-plan-missing"})
                    continue
                fd = os.open(plan, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
                with os.fdopen(fd, "rb") as stream:
                    info = os.fstat(stream.fileno())
                    if not stat.S_ISREG(info.st_mode):
                        _fail("not-regular-file")
                    sample = stream.read(65536)
                if info.st_size > len(sample):
                    diagnostics.append({"id": child.name, "code": "active-plan-truncated"})
                if needle in sample.decode("utf-8", "replace").casefold():
                    entries.append(row)
            except OSError:
                diagnostics.append({"id": child.name, "code": "active-entry-unreadable"})
    if state in ("archived", "all"):
        for id, entry in sorted(catalog["entries"].items()):
            if entry["state"] != "archived":
                continue
            card = entry["card"]
            links = card["delivery_links"] + card["verification_links"]
            haystack = " ".join([id, card["title"], card["purpose"], card["accepted_result"]] +
                                card["exclusions"] + card["reusable_decisions"] +
                                [part for link in links for part in (link["label"], link["path"])])
            if needle is None or needle in haystack.casefold():
                entries.append({"id": id, "path": str(root / entry["archive"]), "state": "archived", "card": card})
    return {"entries": entries, "pending": pending, "diagnostics": diagnostics}


def resolve(repo, id, relative="plan.md"):
    """Read one requested member by logical id or exact recorded source prefix."""
    root = _real_root(repo)
    if type(id) is not str:
        _fail("invalid-id")
    relative = _safe_rel(relative).as_posix()
    for row in _pending(root):
        if id == row["id"] or id == _expected_original_rel(row["id"]):
            _fail("pending-transaction")
    catalog, _, _ = _read_catalog(root)
    entry = catalog["entries"].get(id)
    if entry is None:
        entry = next((row for row in catalog["entries"].values() if row["original"] == id), None)
    if entry is not None:
        base = _path(root, entry["archive"] if entry["state"] == "archived" else entry["original"], must_exist=True)
        expected = entry["inventory"]
        if relative not in expected or expected[relative]["kind"] == "directory":
            _fail("invalid-member")
        raw = _member_file(base, relative, expected)
    else:
        _safe_id(id, allow_unknown=True)
        base = root / "docs/plans" / id
        if not base.exists() or base.is_symlink() or not base.is_dir():
            raise FileNotFoundError(str(base / relative))
        raw = _member_file(base, relative, None)
    return {"path": str(base / relative), "bytes": raw, "sha256": _digest(raw)}


def preview(repo, id, qualification):
    """Validate a selected closed workspace and return a no-effect pinned proposal."""
    root = _real_root(repo)
    id = _safe_id(id)
    if _pending(root):
        _fail("pending-transaction")
    source, destination = _workspace_paths(root, id)
    if source.is_symlink() or not source.is_dir():
        _fail("workspace-not-active")
    if destination.exists() or destination.is_symlink():
        _fail("destination-occupied")
    catalog, cat_sha, index_sha = _read_catalog(root)
    if id in catalog["entries"]:
        _fail("duplicate-id")
    inventory, revision = _qualify(root, source, id, qualification)
    return {"id": id, "origin": str(source), "destination": str(destination),
            "source_revision": revision, "inventory": inventory,
            "catalog_sha256": cat_sha, "index_sha256": index_sha,
            "qualification": qualification,
            "qualification_sha256": _digest(_canonical(qualification))}


def apply(repo, preview, *, scope, writer_receipt):
    """Archive exactly one workspace whose preview and writer scope still match."""
    root = _real_root(repo)
    _exact(preview, {"id", "origin", "destination", "source_revision", "inventory", "catalog_sha256",
                     "index_sha256", "qualification", "qualification_sha256"}, "preview")
    id = _safe_id(preview["id"])
    _refuse_pending_writer(root)
    source, destination = _workspace_paths(root, id)
    if str(source) != preview["origin"] or str(destination) != preview["destination"]:
        _fail("preview-path-mismatch")
    if _revision(preview["inventory"]) != preview["source_revision"]:
        _fail("invalid-preview-revision")
    _exact(preview["qualification"], QUALIFICATION_KEYS, "qualification")
    if preview["qualification"]["id"] != id or preview["qualification"]["source_revision"] != preview["source_revision"] or _digest(_canonical(preview["qualification"])) != preview["qualification_sha256"]:
        _fail("invalid-preview-qualification")
    scope_hash = _scope(root, id, scope, "archive")
    writer_hash = _writer(root, id, preview["source_revision"], scope_hash, writer_receipt, "archive")
    catalog, cat_sha, index_sha = _read_catalog(root)
    existing = catalog["entries"].get(id)
    if existing and existing["state"] == "archived":
        if existing["revision"] != preview["source_revision"] or existing["inventory"] != preview["inventory"] or existing["qualification"] != preview["qualification_sha256"] or source.exists() or source.is_symlink() or not _check_tree(root, destination, existing["inventory"]):
            _fail("completed-operation-mismatch")
        with _locked(root, destination):
            current, current_cat_sha, current_index_sha = _metadata_state(root)
            if current_cat_sha != cat_sha or current_index_sha != index_sha or current["entries"].get(id) != existing or source.exists() or source.is_symlink() or not _check_tree(root, destination, existing["inventory"]):
                _fail("completed-operation-mismatch")
            _revalidate_authority(root, id, preview["source_revision"], scope, writer_receipt, "archive", scope_hash, writer_hash)
            return _result(id, "archived", destination, existing["revision"], "already-applied")
    if cat_sha != preview["catalog_sha256"] or index_sha != preview["index_sha256"] or existing is not None:
        _fail("stale-catalog")
    if source.is_symlink() or not source.is_dir() or destination.exists() or destination.is_symlink():
        _fail("workspace-drift")
    with _locked(root, source):
        catalog, current_cat_sha, current_index_sha = _metadata_state(root)
        if current_cat_sha != preview["catalog_sha256"] or current_index_sha != preview["index_sha256"]:
            _fail("stale-catalog")
        current = _inventory(source)
        if current != preview["inventory"] or _revision(current) != preview["source_revision"]:
            _fail("stale-source")
        _require_same_filesystem(source.parent, destination.parent)
        _qualify(root, source, id, preview["qualification"])
        next_catalog = {"schema": CATALOG_SCHEMA, "entries": dict(catalog["entries"])}
        next_catalog["entries"][id] = {"id": id, "original": _expected_original_rel(id),
            "archive": _expected_archive_rel(id), "state": "archived", "revision": preview["source_revision"],
            "inventory": preview["inventory"], "qualification": preview["qualification_sha256"],
            "card": preview["qualification"]["card"]}
        _revalidate_authority(root, id, preview["source_revision"], scope, writer_receipt, "archive", scope_hash, writer_hash)
        tx = _transaction(root, "archive", id, source, destination, preview["source_revision"],
                          preview["inventory"], current_cat_sha, current_index_sha, next_catalog,
                          scope_hash, writer_hash)
        _write_journal(root, tx)
        if destination.exists() or destination.is_symlink():
            _fail("occupied-destination")
        os.rename(source, destination)
        _fsync_dir(source.parent)
        _fsync_dir(destination.parent)
        _publish_next(root, tx)
        if not _check_tree(root, destination, preview["inventory"]):
            _fail("post-move-inventory-mismatch")
        _verify_published(root, tx)
        _remove_journal(root)
    return _result(id, "archived", destination, preview["source_revision"], "applied")


def recover(repo, *, scope, writer_receipt):
    """Finish one observed journal under fresh scoped authority, or report no-op."""
    root = _real_root(repo)
    tx = _read_transaction(root)
    if tx is None:
        return _result(None, None, None, None, "no-op")
    id = tx["id"]
    scope_hash = _scope(root, id, scope, "recover")
    writer_hash = _writer(root, id, tx["source_revision"], scope_hash, writer_receipt, "recover")
    origin, destination = Path(tx["origin"]), Path(tx["destination"])
    if (origin.exists() and not origin.is_symlink()) == (destination.exists() and not destination.is_symlink()):
        _fail("location-conflict")
    carrier = origin if origin.exists() else destination
    with _locked(root, carrier):
        if _read_transaction(root) != tx:
            _fail("transaction-drift")
        if _scope(root, id, scope, "recover") != scope_hash or _writer(root, id, tx["source_revision"], scope_hash, writer_receipt, "recover") != writer_hash:
            _fail("recovery-authority-drift")
        _settled_inventory(_inventory(carrier))
        return _finish_transaction(root, tx)


def restore(repo, id, expected_revision, *, scope, writer_receipt):
    """Restore one archived workspace without overwriting a current destination."""
    root = _real_root(repo)
    id = _safe_id(id)
    _hex(expected_revision, "expected-revision")
    _refuse_pending_writer(root)
    active, archived = _workspace_paths(root, id)
    catalog, cat_sha, index_sha = _read_catalog(root)
    entry = catalog["entries"].get(id)
    if entry is None:
        _fail("not-archived")
    if entry["revision"] != expected_revision:
        _fail("stale-archive")
    scope_hash = _scope(root, id, scope, "restore")
    writer_hash = _writer(root, id, expected_revision, scope_hash, writer_receipt, "restore")
    if entry["state"] == "active":
        if archived.exists() or archived.is_symlink() or not _check_tree(root, active, entry["inventory"]):
            _fail("completed-operation-mismatch")
        with _locked(root, active):
            current, current_cat_sha, current_index_sha = _metadata_state(root)
            if current_cat_sha != cat_sha or current_index_sha != index_sha or current["entries"].get(id) != entry or archived.exists() or archived.is_symlink() or not _check_tree(root, active, entry["inventory"]):
                _fail("completed-operation-mismatch")
            _revalidate_authority(root, id, expected_revision, scope, writer_receipt, "restore", scope_hash, writer_hash)
            return _result(id, "active", active, entry["revision"], "already-restored")
    if not _check_tree(root, archived, entry["inventory"]):
        _fail("stale-archive")
    if active.exists() or active.is_symlink():
        _fail("occupied-destination")
    with _locked(root, archived):
        current_catalog, current_cat_sha, current_index_sha = _metadata_state(root)
        current_entry = current_catalog["entries"].get(id)
        if current_cat_sha != cat_sha or current_index_sha != index_sha or current_entry != entry:
            _fail("stale-catalog")
        if not _check_tree(root, archived, entry["inventory"]):
            _fail("stale-archive")
        _settled_inventory(entry["inventory"])
        _require_same_filesystem(archived.parent, active.parent)
        next_catalog = {"schema": CATALOG_SCHEMA, "entries": dict(current_catalog["entries"])}
        next_catalog["entries"][id] = dict(entry, state="active")
        _revalidate_authority(root, id, expected_revision, scope, writer_receipt, "restore", scope_hash, writer_hash)
        tx = _transaction(root, "restore", id, archived, active, expected_revision, entry["inventory"],
                          current_cat_sha, current_index_sha, next_catalog, scope_hash, writer_hash)
        _write_journal(root, tx)
        if active.exists() or active.is_symlink():
            _fail("occupied-destination")
        os.rename(archived, active)
        _fsync_dir(archived.parent)
        _fsync_dir(active.parent)
        _publish_next(root, tx)
        if not _check_tree(root, active, entry["inventory"]):
            _fail("post-restore-inventory-mismatch")
        _verify_published(root, tx)
        _remove_journal(root)
    return _result(id, "active", active, expected_revision, "restored")
