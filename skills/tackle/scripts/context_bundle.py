import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def document(title, value):
    return ("# " + title + "\n\n```json\n" +
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n```\n").encode()


def decode(data):
    return json.loads(data.decode().split("```json\n", 1)[1].rsplit("\n```", 1)[0])


class Context:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        self.board_name = "task-board.md"
        self.history_name = "history.md"
        self.archive_name = "history-archive.md"
        self.projection_name = "current-work.md"
        self.handoff_name = "handoff-brief.md"
        older = [name for name in ("board.md", "log.md", "log-archive.md", "coordinator.md", "HANDOFF.md")
                 if (self.root / name).exists()]
        if older:
            raise ValueError("migrate first: older workspace path " + older[0] +
                             " (references/guides/migrate.md#forward-only)")
        board = self.root / self.board_name
        if board.is_file() and b"Schema: tackle-workspace/5" not in board.read_bytes().split(b"\n"):
            raise ValueError("migrate first: task-board.md has no tackle-workspace/5 schema line with LF line "
                             "endings (references/guides/migrate.md#forward-only)")
        self.bytes_read = self.bytes_written = self.metadata_checks = 0

    def path(self, name):
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError("unsafe workspace path")
        path = self.root / relative
        for part in [path, *path.parents]:
            if part == self.root:
                break
            if part.is_symlink():
                raise ValueError("symlink is not an authorized source")
        if path.resolve().is_relative_to(self.root) is False:
            raise ValueError("unsafe workspace path")
        return path

    def read(self, name):
        data = self.path(name).read_bytes()
        self.bytes_read += len(data)
        return data

    def write(self, name, data):
        path = self.path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, staged = tempfile.mkstemp(prefix=".context-", dir=path.parent)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(data)
                self.bytes_written += len(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(staged, path)
            self.sync(path.parent)
        finally:
            if os.path.exists(staged):
                os.unlink(staged)

    @staticmethod
    def sync(directory):
        handle = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(handle)
        finally:
            os.close(handle)

    @contextmanager
    def writer(self):
        import fcntl
        with self.path(".context-lock").open("a+b") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("writer active") from error
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    @contextmanager
    def reader(self):
        import fcntl
        path = self.path(".context-lock")
        if not path.exists():
            yield
            return
        with path.open("rb") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("writer active") from error
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    @staticmethod
    def events(data):
        positions = [m.start() for m in re.finditer(rb"(?m)^## [0-9]{4}-[0-9]{2}-[0-9]{2}[^\n]*\n", data)]
        if not positions:
            raise ValueError("history has no complete event heading")
        chunks = [data[a:b] for a, b in zip(positions, positions[1:] + [len(data)])]
        dates = [chunk[3:13] for chunk in chunks]
        if dates != sorted(dates):
            raise ValueError("history out of order")
        return data[:positions[0]], chunks

    def pending(self):
        if self.path("history/transaction.md").exists():
            raise ValueError("incomplete maintenance; recover before reuse")

    def index(self):
        if self.path("history/index.md").exists():
            index = decode(self.read("history/index.md"))
        else:
            index = {"schema": "tackle-history/1", "segments": []}
            if self.path(self.archive_name).exists():
                data = self.read(self.archive_name)
                index["segments"].append(self.segment(self.archive_name, data, 1))
        if index.get("schema") != "tackle-history/1":
            raise ValueError("unknown history schema")
        start, prior_date = 1, ""
        for segment in index["segments"]:
            self.metadata_checks += 1
            path = self.path(segment["path"])
            if not path.is_file():
                raise ValueError("missing archive: " + segment["path"])
            if (segment["first"] != start or segment["last"] < start or
                    path.stat().st_size != segment["bytes"]):
                raise ValueError("corrupt archive index or size")
            if segment["first_date"] < prior_date or segment["last_date"] < segment["first_date"]:
                raise ValueError("history out of order")
            start, prior_date = segment["last"] + 1, segment["last_date"]
        return index

    def segment(self, name, data, first):
        _, entries = self.events(data)
        return {"path": name, "sha256": digest(data), "bytes": len(data), "first": first,
                "last": first + len(entries) - 1,
                "first_date": entries[0][3:13].decode(), "last_date": entries[-1][3:13].decode()}

    def sealed(self, segment):
        data = self.read(segment["path"])
        if digest(data) != segment["sha256"] or self.segment(segment["path"], data, segment["first"]) != segment:
            raise ValueError("corrupt archive: " + segment["path"])
        return data

    def snapshot(self, scope, sources):
        self.pending()
        names = sorted(set(sources))
        if not {self.board_name, "decisions.md", "questions.md"}.issubset(names):
            raise ValueError("current authority sources missing")
        if any(name in names for name in [self.projection_name, self.handoff_name, "inventory.md",
                                          "history/transaction.md", ".context-lock"]):
            raise ValueError("projection cannot be its own authority")
        source_bytes = {name: self.read(name) for name in names}
        index = self.index()
        log = self.read(self.history_name)
        _, active = self.events(log)
        closed = index["segments"][-1]["last"] if index["segments"] else 0
        if index["segments"] and active[0][3:13].decode() < index["segments"][-1]["last_date"]:
            raise ValueError("history out of order")
        revisions = {name: digest(data) for name, data in source_bytes.items()}
        return {"schema": "tackle-current-work/1", "scope": scope, "revisions": revisions,
                "state_revision": digest(json.dumps(revisions, sort_keys=True).encode()),
                "history_revision": digest(document("History index", index)),
                "active_history_revision": digest(log), "last_event": closed + len(active),
                "last_event_revision": digest(active[-1]),
                "sources": {name: data.decode("utf-8") for name, data in source_bytes.items()}}

    def project(self, scope, sources):
        with self.writer():
            projection = self.snapshot(scope, sources)
            self.write(self.projection_name, document("Current work — verified source projection", projection))
            return projection

    def current(self, scope, sources):
        with self.reader():
            actual = self.snapshot(scope, sources)
            projection = decode(self.read(self.projection_name))
            if projection.get("sources") != actual["sources"]:
                if projection.get("revisions") == actual["revisions"]:
                    raise ValueError("projection source mismatch")
                raise ValueError("stale current-work projection")
            if projection != actual:
                raise ValueError("stale current-work projection")
            return projection

    def last_event(self):
        self.pending()
        index = self.index()
        return (index["segments"][-1]["last"] if index["segments"] else 0) + len(self.events(self.read(self.history_name))[1])

    def history(self):
        with self.reader():
            self.pending()
            index = self.index()
            prefix, active = self.events(self.read(self.history_name))
            result = prefix + b"".join(self.sealed(s) for s in index["segments"]) + b"".join(active)
            self.events(result)
            return result

    def event(self, number):
        with self.reader():
            self.pending()
            index = self.index()
            for segment in index["segments"]:
                if segment["first"] <= number <= segment["last"]:
                    return self.events(self.sealed(segment))[1][number - segment["first"]]
            closed = index["segments"][-1]["last"] if index["segments"] else 0
            entries = self.events(self.read(self.history_name))[1]
            if type(number) is int and 1 <= number - closed <= len(entries):
                return entries[number - closed - 1]
            raise ValueError("missing event")

    def lookup(self, heading):
        matches = [entry for entry in self.events(self.history())[1]
                   if entry.split(b"\n", 1)[0].decode().rstrip("\r") == heading]
        if len(matches) != 1:
            raise ValueError("missing or ambiguous original heading")
        return matches[0]

    def append_event(self, data, expected_event, expected_revision):
        prefix, new_entries = self.events(data)
        if prefix or len(new_entries) != 1:
            raise ValueError("append requires one original event")
        with self.writer():
            self.pending()
            index = self.index()
            old_log = self.read(self.history_name)
            _, entries = self.events(old_log)
            number = (index["segments"][-1]["last"] if index["segments"] else 0) + len(entries)
            if number == expected_event + 1 and entries[-1] == data:
                return False
            if number != expected_event or digest(entries[-1]) != expected_revision:
                raise ValueError("history head changed; reconcile before appending")
            if data[3:13] < entries[-1][3:13]:
                raise ValueError("history out of order")
            self.write(self.history_name, old_log + data)
            return True

    def archive(self, keep=5, segment_bytes=65536, fail_after=None):
        if type(keep) is not int or keep < 1 or type(segment_bytes) is not int or segment_bytes < 1:
            raise ValueError("invalid archive policy")
        with self.writer():
            self.pending()
            index = self.index()
            for segment in index["segments"]:
                self.sealed(segment)
            old_log = self.read(self.history_name)
            prefix, entries = self.events(old_log)
            if len(entries) <= keep:
                return False
            groups, group = [], b""
            for entry in entries[:-keep]:
                if group and len(group) + len(entry) > segment_bytes:
                    groups.append(group)
                    group = b""
                group += entry
            groups.append(group)
            new_index = json.loads(json.dumps(index))
            first = index["segments"][-1]["last"] + 1 if index["segments"] else 1
            for data in groups:
                name = "history/segment-" + digest(data) + ".md"
                if self.path(name).exists():
                    if self.read(name) != data:
                        raise ValueError("archive content collision")
                else:
                    self.write(name, data)
                    self.path(name).chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
                segment = self.segment(name, data, first)
                new_index["segments"].append(segment)
                first = segment["last"] + 1
            self.stop(fail_after, "segment")
            old_index = self.read("history/index.md") if self.path("history/index.md").exists() else None
            transaction = {"old_log": digest(old_log), "old_index": digest(old_index) if old_index else None,
                           "next_log": base64.b64encode(prefix + b"".join(entries[-keep:])).decode(),
                           "next_index": new_index, "old_segments": index["segments"],
                           "moved_segments": new_index["segments"][len(index["segments"]):]}
            self.write("history/transaction.md", document("Pending history maintenance", transaction))
            self.stop(fail_after, "journal")
            self.finish(transaction, fail_after)
            return True

    @staticmethod
    def stop(requested, phase):
        if requested == phase:
            raise RuntimeError("injected interruption at " + phase)

    def finish(self, transaction, fail_after=None):
        next_log = base64.b64decode(transaction["next_log"], validate=True)
        next_index = document("History index", transaction["next_index"])
        current_log = self.read(self.history_name)
        current_index = self.read("history/index.md") if self.path("history/index.md").exists() else None
        if (digest(current_log) not in [transaction["old_log"], digest(next_log)] or
                (digest(current_index) if current_index else None) not in [transaction["old_index"], digest(next_index)]):
            raise ValueError("history changed during maintenance; reconcile original records")
        if transaction["next_index"]["segments"] != transaction["old_segments"] + transaction["moved_segments"]:
            raise ValueError("maintenance index lineage mismatch")
        checked = {segment["path"]: self.sealed(segment) for segment in transaction["next_index"]["segments"]}
        prefix, entries = self.events(next_log)
        reconstructed = prefix + b"".join(checked[s["path"]] for s in transaction["moved_segments"]) + b"".join(entries)
        if digest(reconstructed) != transaction["old_log"]:
            raise ValueError("maintenance originals mismatch")
        self.events(reconstructed)
        if current_index != next_index:
            self.write("history/index.md", next_index)
        self.stop(fail_after, "index")
        if current_log != next_log:
            self.write(self.history_name, next_log)
        self.stop(fail_after, "log")
        self.path("history/transaction.md").unlink()
        self.sync(self.path("history"))

    def recover(self):
        with self.writer():
            if not self.path("history/transaction.md").exists():
                return False
            self.finish(decode(self.read("history/transaction.md")))
            return True

    def export(self, scope, sources, destination, event_numbers=(), record_bundles=None):
        with self.reader():
            return self.export_locked(scope, sources, destination, event_numbers, record_bundles)

    def export_locked(self, scope, sources, destination, event_numbers, record_bundles):
        projection = self.current(scope, sources)
        if any(type(number) is not int or not 1 <= number <= projection["last_event"] for number in event_numbers):
            raise ValueError("requested event outside checkpoint")
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=False)
        bundle = Context(destination)
        for name, value in projection["sources"].items():
            bundle.write(name, value.encode())
        for number in sorted(set(event_numbers)):
            bundle.write("history/event-" + str(number) + ".md", self.event(number))
        for prefix, exported in (record_bundles or {}).items():
            exported = Path(exported).resolve(strict=True)
            for path in sorted(exported.rglob("*")):
                name = str(Path(prefix) / path.relative_to(exported))
                if path.is_symlink() or path.is_file():
                    target = bundle.path(name)
                    if target.exists() or target.is_symlink() or name in [self.handoff_name, "inventory.md"]:
                        raise ValueError("record bundle path collision")
                    if path.is_symlink():
                        link = os.readlink(path)
                        if (path.name not in ["blobs", "stdout.bin", "stderr.bin"] or
                                Path(link).is_absolute() or not path.resolve(strict=True).is_relative_to(exported)):
                            raise ValueError("unsafe record alias")
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.symlink_to(link)
                        self.bytes_read += len(link.encode())
                        bundle.bytes_written += len(link.encode())
                    else:
                        data = path.read_bytes()
                        self.bytes_read += len(data)
                        bundle.write(name, data)
        bundle.write(self.handoff_name, document("Portable current work", projection))
        if self.snapshot(scope, sources) != projection:
            raise ValueError("sources changed during handoff")
        inventory = bundle.file_inventory()
        bundle.write("inventory.md", document("Handoff inventory", inventory))
        self.bytes_read += bundle.bytes_read
        self.bytes_written += bundle.bytes_written
        verified = self.verify_export(destination)
        self.bytes_read += verified["bytes_read"]
        return destination

    def file_inventory(self):
        inventory = {}
        for path in sorted(self.root.rglob("*")):
            if path == self.root / "inventory.md":
                continue
            name = str(path.relative_to(self.root))
            if path.is_symlink():
                target = os.readlink(path)
                if Path(target).is_absolute() or not path.resolve(strict=True).is_relative_to(self.root):
                    raise ValueError("export inventory unsafe alias")
                self.bytes_read += len(target.encode())
                inventory[name] = "symlink:" + target
            elif path.is_file():
                inventory[name] = digest(self.read(name))
        return inventory

    @staticmethod
    def verify_export(destination):
        bundle = Context(destination)
        inventory = decode(bundle.read("inventory.md"))
        actual = bundle.file_inventory()
        if actual != inventory:
            raise ValueError("export inventory mismatch")
        projection = decode(bundle.read(bundle.handoff_name))
        if set(projection["sources"]) != set(projection["revisions"]):
            raise ValueError("export source membership mismatch")
        for name, revision in projection["revisions"].items():
            data = bundle.read(name)
            if digest(data) != revision or data.decode("utf-8") != projection["sources"][name]:
                raise ValueError("export source text/revision mismatch")
        return {"projection": projection, "inventory": inventory, "bytes_read": bundle.bytes_read}
