"""Stage and capture method-only behavioral smoke trials, never installed."""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODEX = "/Applications/ChatGPT.app/Contents/Resources/codex"

ROUTING_TASKS = [
    "Restore the specified one-line whitespace trimming in src/format.py. Existing tests and spec already require trimming. One product file, under ten lines, one session, no new feature, dependencies, security concerns, shared state or integration. No handoff. No durable plan was requested.",
    "Plan one new internal input check and its tests in a single module, one session, two Points. It is a new bounded feature, not a restoration. No public API, dependencies, shared state, security concerns, multi-track uncertainty or handoff. Choose the smallest eligible route.",
    "Plan a public API response-contract change in one module and one session. Two Points cover implementation and integration; no other risks. A teammate proposes Lite because there are only two Points. Choose the route.",
    "Plan an internal change in one module, two Points. Work spans two sessions and must be handed to another team tomorrow. A teammate proposes Lite due to the Point count. Choose the route.",
    "Right-size an existing Full plan: four Points were just merged into two after a provisional Ready observation. The public API response change remains in scope. Choose the route and record what happens to readiness and affected coverage/contracts.",
    "The owner explicitly requests a Full plan for a one-session, one-file, one-line internal correction with no risks. Choose the route.",
    "Right-size an existing Full plan. The owner removed the public API change entirely; now there is only a bounded new internal check and its tests, one module, one session, two Points, no handoff or other risk. A provisional Ready result described the old scope. Choose the route and record the scope-change reason and readiness consequences.",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def stage(destination):
    destination.mkdir(parents=True, exist_ok=False)
    manifest = {"created": stamp(), "kind": "method-only smoke, one seed per case", "cases": []}
    release = json.loads((ROOT / "eval/validation-integrity/release-scope/cases.json").read_text())
    for index, task in enumerate(ROUTING_TASKS + release, 1):
        case = destination / f"case-{index:02}"
        case.mkdir()
        shutil.copyfile(ROOT / "SKILL.md", case / "SKILL.md")
        shutil.copytree(ROOT / "references", case / "references")
        write(case / "src/format.py", "def format_value(value):\n    return value\n")
        source_hash = digest(case / "src/format.py")
        if isinstance(task, str):
            prompt = ("This is a route-selection/readiness exercise, not execution or full scaffolding. Before deciding, read SKILL.md, references/guides/intake-and-gate.md and references/guides/decompose-and-lint.md in full. The four intake anchors are already confirmed by the owner in this bounded task. Do not change product source or create a plan workspace; the only requested artifact is decision.json with route, reason, readiness and affected_checks fields.\n\n" + task)
            family, ordinal = "routing", index
        else:
            family, ordinal = "release", index - len(ROUTING_TASKS)
            selected = ["docs/plans/current"] if task["scope_known"] else None
            active_other = task.get("other_active_failure", False)
            status = "🟡" if task["board_has_in_progress"] else ("🟢" if task["all_points_complete"] else "⏸")
            subject = "current" if task["selected"] else "older"
            if subject == "older":
                workspaces = [("current", "🟢", True, False), (subject, status, task["global_acceptance"], True)]
            else:
                workspaces = [(subject, status, task["global_acceptance"], False)]
            if active_other:
                workspaces.append(("other", "🟡", True, True))
            inputs = {"explicit_scope": selected, "self_lint_and_catalog": "already passed in this simulated upstream phase", "workspaces": []}
            for name, state, passes, lint_failure in workspaces:
                workspace = case / "docs/plans" / name
                write(workspace / "board.md", "| Point | What | Briefing | Depends on | Status | Confidence |\n| P-01 | Fixture | points/P-01.md | none | " + state + " | E1 |\n")
                write(workspace / "checks.sh", "#!/bin/sh\ncase \"$1\" in\n lint) exit " + str(int(lint_failure)) + ";;\n done) exit 0;;\n global) test \"$(cat deliverable.txt)\" = accepted;;\n *) exit 2;;\nesac\n")
                stale = task["evidence_stale"] and name == subject
                write(workspace / "deliverable.txt", "accepted\n" if passes and not stale else "unaccepted\n")
                receipt = {"deliverable_sha256": digest(workspace / "deliverable.txt") if not stale else "previous-revision", "previous_global_exit": 0 if passes else 1}
                write(workspace / "previous-receipt.json", json.dumps(receipt) + "\n")
                inputs["workspaces"].append(str(workspace.relative_to(case)))
            write(case / "inputs.json", json.dumps(inputs, indent=2) + "\n")
            prompt = ("This is the workspace-selection/global-acceptance phase of a simulated release, not a real publication. Read SKILL.md, references/guides/lint-spec.md and references/guides/run.md in full. The upstream self-lint and catalog gates are fixture inputs already passed; do not re-run them or scaffold missing upstream artifacts. inputs.json names all discovered workspaces and the owner's explicit selection if supplied. For each discovered workspace, run its checks.sh lint and checks.sh done from that workspace and inspect board.md. Evaluate current global acceptance where required using checks.sh global and deliverable hashes versus previous-receipt.json. These executable fixture checks stand in for upstream stage outputs; do not edit checks, inputs, boards or deliverables. No waiver is authorized. Write decision.json with allowed, reason, gating_workspaces, numerator and denominator for the sweep (include the 8 upstream self-lint gates + 1 catalog). If and only if the release is acceptable, write RELEASE_APPROVED containing 'simulated only'. The owner authorizes this disposable marker, never a real tag, push or network publication. If selection is unknown, record the smallest missing decision in your result.")
        write(case / "TASK.md", prompt + "\n")
        manifest["cases"].append({"id": case.name, "family": family, "ordinal": ordinal, "source_sha256": source_hash, "inputs": {str(p.relative_to(case)): digest(p) for p in case.rglob("*") if p.is_file()}})
    write(destination / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    return manifest


def run_case(destination, entry, output):
    case = destination / entry["id"]
    result_dir = output / entry["id"]
    result_dir.mkdir(parents=True, exist_ok=False)
    artifacts = result_dir / "artifacts"
    artifacts.mkdir()
    image = "sha256:866dac7948f23ddd2260ea5e80ebdec3cc92ac50eadb020ecfa0632854013be3"
    base = ["docker", "run", "--rm", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--tmpfs", "/tmp", "--tmpfs", "/root", "--mount", f"type=bind,src={case},dst=/fixture,readonly", "--mount", f"type=bind,src={artifacts},dst=/outputs", "--workdir", "/fixture"]
    probe_cmd = base + ["--network", "none", image, "sh", "-c", "test -r SKILL.md && ! test -e /Users/alph0x/Developer/Tackle && touch /outputs/allowed && ! touch /fixture/protected-probe && ! touch /outside-probe"]
    probe = subprocess.run(probe_cmd, capture_output=True)
    write(result_dir / "isolation-probe.json", json.dumps({"command": probe_cmd, "exit": probe.returncode, "stdout": probe.stdout.decode(), "stderr": probe.stderr.decode()}, indent=2))
    if probe.returncode:
        return {"id": entry["id"], "isolation": "unavailable", "exit": probe.returncode}
    argv = base + ["--mount", f"type=bind,src={Path.home() / '.codex/auth.json'},dst=/root/.codex/auth.json,readonly", image, "codex", "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check", "--sandbox", "danger-full-access", "--add-dir", "/outputs", "--json", "--color", "never", "--cd", "/fixture", "-m", "gpt-6-astra", "-c", 'model_reasoning_effort="high"', "Read TASK.md and perform only that task. Use only /fixture inputs and skill, no external lookup or delegation. All inputs are physically read-only. Write requested decision.json and any permitted marker under /outputs/ (not /fixture). Do not access authentication files. Work autonomously within this bounded exercise."]
    shutil.copyfile(Path(__file__), result_dir / "runner.py")
    record = {"id": entry["id"], "command": argv, "cwd": str(case), "start": stamp(), "runner_sha256": digest(Path(__file__)), "inputs_before": entry["inputs"], "isolation": "Linux container: only task fixture read-only, artifacts writable, auth read-only; no repository, oracle, home or siblings mounted"}
    with (result_dir / "events.jsonl").open("wb") as stdout, (result_dir / "stderr").open("wb") as stderr:
        try:
            result = subprocess.run(argv, cwd=case, stdout=stdout, stderr=stderr, timeout=600)
            record["exit"] = result.returncode
        except subprocess.TimeoutExpired:
            record.update(exit=None, timeout_seconds=600)
    record["end"] = stamp()
    record["inputs_after"] = {name: digest(case / name) if (case / name).is_file() else None for name in entry["inputs"]}
    record["artifacts"] = {str(p.relative_to(artifacts)): digest(p) for p in artifacts.rglob("*") if p.is_file()}
    write(result_dir / "record.json", json.dumps(record, indent=2) + "\n")
    for name in ("decision.json", "RELEASE_APPROVED"):
        if (artifacts / name).is_file():
            shutil.copyfile(artifacts / name, result_dir / name)
    return {"id": entry["id"], "exit": record["exit"], "artifacts": list(record["artifacts"])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["stage", "run"])
    parser.add_argument("destination", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--exclude")
    parser.add_argument("--family", choices=["routing", "release"])
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    if args.mode == "stage":
        manifest = stage(args.destination)
        print(json.dumps({"destination": str(args.destination), "cases": len(manifest["cases"])}))
        return
    manifest = json.loads((args.destination / "manifest.json").read_text())
    entries = [e for e in manifest["cases"] if (args.case is None or e["id"] == args.case) and e["id"] != args.exclude and (args.family is None or e["family"] == args.family)]
    args.output.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(lambda entry: run_case(args.destination, entry, args.output), entries):
            print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
