"""Synthetic logical-I/O comparison, including preparation and reconstruction.

These are controlled algorithms, not observed agent episodes or filesystem block-I/O.
"""
import json
from pathlib import Path
import tempfile
import shutil
from test_context import fixture, recipe


def size(root):
    files = [p for p in root.rglob("*") if p.is_file()]
    return {"retained_bytes": sum(p.stat().st_size for p in files), "files": len(files)}


def measure(context, operation):
    before = (context.bytes_read, context.bytes_written, context.metadata_checks)
    result = operation()
    return result, dict(zip(["bytes_read", "bytes_written", "archive_metadata_checks"],
                            [context.bytes_read - before[0], context.bytes_written - before[1],
                             context.metadata_checks - before[2]]))


def sample(count):
    api = recipe()
    scope = {"tasks": ["P-01"], "requirements": ["R01"], "milestone": "M1"}
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "workspace"
        root.mkdir()
        sources, events = fixture(root, count)
        with (root / "board.md").open("a") as stream:
            for number in range(count):
                stream.write(f"P-C{number:04}: Complete; record retained in original history\n")
        initial = size(root)
        event = f"## 2026-09-02 - session {count+1} - active task update\nIn progress P-01; no acceptance inferred.\n".encode()
        legacy_root = Path(temp) / "legacy"
        shutil.copytree(root, legacy_root)
        legacy = api["Context"](legacy_root)
        def legacy_resume():
            for name in sources:
                legacy.read(name)
            legacy.events(legacy.read("log.md"))[-1][-1]
        _, baseline_resume = measure(legacy, legacy_resume)
        def legacy_update():
            board = legacy.read("board.md")
            legacy.write("board.md", board.replace(b"Checking", b"In progress", 1))
            with (legacy_root / "log.md").open("ab") as stream:
                stream.write(event)
                legacy.bytes_written += len(event)
        _, baseline_update = measure(legacy, legacy_update)
        def legacy_handoff():
            combined = b"".join(legacy.read(name) for name in sources + ["log.md"])
            legacy.write("HANDOFF.md", combined)
        _, baseline_handoff = measure(legacy, legacy_handoff)
        _, baseline_retrieval = measure(legacy, lambda: legacy.event(1))
        _, baseline_reconstruction = measure(legacy, legacy.history)
        baseline = {"resume": baseline_resume, "task_update": baseline_update, "handoff": baseline_handoff,
                    "named_archived_failure_retrieval": baseline_retrieval,
                    "complete_history_reconstruction": baseline_reconstruction}
        context = api["Context"](root)
        _, archive = measure(context, lambda: context.archive(keep=5, segment_bytes=65536))
        projection, build = measure(context, lambda: context.project(scope, sources))
        _, resume = measure(context, lambda: context.current(scope, sources))
        def update():
            content = context.read("board.md")
            context.write("board.md", content.replace(b"Checking", b"In progress", 1))
            context.append_event(event, projection["last_event"], projection["last_event_revision"])
            context.project(scope, sources)
        _, update_cost = measure(context, update)
        _, handoff = measure(context, lambda: context.export(scope, sources, Path(temp) / "handoff"))
        _, retrieval = measure(context, lambda: context.event(1))
        reconstructed, reconstruction = measure(context, context.history)
        assert reconstructed == b"# History\n\n" + b"".join(events) + event
        result = {"closed_tasks": count, "initial": initial,
                  "baseline": baseline,
                  "candidate": {"archive_and_index": archive, "projection_build": build,
                                "resume": resume, "task_update": update_cost, "handoff": handoff,
                                "named_archived_failure_retrieval": retrieval,
                                "complete_history_reconstruction": reconstruction,
                                "retained": size(root)}}
        for label in ["baseline", "candidate"]:
            stages = result[label]
            included = ["resume", "task_update", "handoff", "named_archived_failure_retrieval",
                        "complete_history_reconstruction"]
            if label == "candidate":
                included += ["archive_and_index", "projection_build"]
            stages["measured_scenario_total"] = {
                key: sum(stages[name][key] for name in included) for key in ["bytes_read", "bytes_written"]}
        return result


def report():
    return {
        "schema": "tackle-context-measurement/1", "kind": "synthetic deterministic logical content I/O",
        "sizes": [sample(n) for n in [10, 100, 1000]],
        "coverage": "Same active task and dependencies; closed task board rows grow with history. All recipe reads, hashing, staged writes, indexing, verification and export writes counted.",
        "baseline": "Pinned 8.1.0 full-history handoff and file-wide latest-entry scan; original task-update append. This is an explicit algorithm comparison, not measured baseline agent behavior.",
        "limitations": [
            "Current board/source verification still grows with authoritative scope; no constant total-cost claim.",
            "Initial indexing, complete reconstruction and named archive retrieval are charged separately and in total, not hidden savings.",
            "Retained bytes grow; archival changes placement and does not retire original records.",
            "Filesystem metadata, kernel cache and journal/block-I/O bytes are not measured; metadata calls are counted separately.",
            "Check-record export costs belong to the record lifecycle benchmark; these fixtures have no additional required raw objects.",
            "No model/token/latency or agent compliance improvement is established by this fixture.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
