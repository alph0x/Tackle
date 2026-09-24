# Codex native usage — optional capture recipe

This recipe reads native Codex Desktop or `codex exec --json` records and appends exact
session-scoped observations to `resource-usage.telemetry.jsonl` in new workspaces; historical
`usage.telemetry.jsonl` remains readable. It is optional: an
unavailable trace does not block task completion, and the provider-independent contract in
[usage-observability.md](usage-observability.md) remains authoritative. It uses only Python's
standard library, reads no authentication file, and does not copy prompt or tool content.

At a role's start and again after its externally observed end, run the fenced Python body with
`python3 - "$workspace" ["$native_jsonl"] <<'PY'` and a closing `PY`, or extract the fence
verbatim into an ephemeral script and give it the same arguments. With no second argument,
`CODEX_THREAD_ID` selects the exact Desktop rollout under `~/.codex/sessions/`. For a saved
CLI stream, pass its JSONL path explicitly. Keep the resulting JSON receipt with the role's
verification record. The recipe writes only the optional sidecar, never the resource usage ledger; record
configured model/effort or an exactly mapped terminal clock in the lifecycle row separately.

Desktop `thread_id` identifies the actor; `session_id` can identify its parent and must not
replace it. A Desktop capture produces the latest thread snapshot and the latest native
observation for each turn. These overlap and must not be added together. CLI completed turns
get distinct ordinal identities.
All observations use session scope and `run_id: n/a`; they are never allocated to a role by
timestamp or fraction. An observed `task_complete` is a terminal **candidate**. Use it as a
role end only when the Run ID maps exactly to that native turn. Model and effort from
`turn_context` are configured bindings, not independent server-model attestations. CLI launch
flags are requested bindings; this stream alone does not attest them or a billing cost.

<!-- codex-usage-recipe:start -->
```python
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path


def fail(message):
    raise SystemExit("codex usage: " + message)


def digest(event):
    raw = json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def metrics(native):
    if not isinstance(native, dict):
        fail("native usage is missing")
    names = {"input_tokens": "input_tokens", "output_tokens": "output_tokens",
             "reasoning_output_tokens": "reasoning_tokens", "cached_input_tokens": "cache_read_tokens",
             "cache_write_input_tokens": "cache_write_tokens"}
    result = {}
    for source, target in names.items():
        if source in native:
            value = native[source]
            if type(value) is not int or value < 0:
                fail("invalid native token count: " + source)
            result[target] = value
    if not result:
        fail("native usage has no supported token counts")
    return result


if len(sys.argv) not in (2, 3):
    fail("use: python3 - <workspace> [native-jsonl]")
workspace = Path(sys.argv[1]).expanduser().resolve()
ledger = workspace / ("resource-usage.md" if (workspace / "resource-usage.md").is_file() else "usage.md")
if (workspace / "resource-usage.md").is_file() and (workspace / "usage.md").exists():
    fail("mixed resource usage paths")
if not workspace.is_dir() or not ledger.is_file():
    fail("workspace with resource usage ledger required")
if "Schema: tackle-observability/2" not in ledger.read_text():
    fail("v2 usage ledger required")

expected_thread = os.environ.get("CODEX_THREAD_ID", "")
if len(sys.argv) == 2:
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", expected_thread):
        fail("exact CODEX_THREAD_ID unavailable; pass native JSONL path")
    matches = list((Path.home() / ".codex/sessions").glob(
        "*/*/*/rollout-*-" + expected_thread + ".jsonl"))
    if len(matches) != 1:
        fail("native thread trace missing or ambiguous")
    trace = matches[0].resolve()
else:
    trace = Path(sys.argv[2]).expanduser().resolve()
if not trace.is_file():
    fail("native JSONL trace missing")

events = []
try:
    with trace.open() as stream:
        for line in stream:
            if line.strip():
                event = json.loads(line)
                if not isinstance(event, dict):
                    fail("non-object native event")
                events.append(event)
except (OSError, UnicodeError, json.JSONDecodeError):
    fail("native JSONL is unreadable or malformed")

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
records = []
desktop = [(i, event) for i, event in enumerate(events)
           if event.get("type") == "token_usage_record"]
cli = [event for event in events if event.get("type") == "turn.completed"]
if desktop and cli:
    fail("mixed Desktop and CLI native formats")
if desktop:
    threads = {event.get("payload", {}).get("thread_id") for _, event in desktop}
    if len(threads) != 1 or not next(iter(threads)):
        fail("ambiguous Desktop thread ID")
    thread = next(iter(threads))
    if expected_thread and thread != expected_thread:
        fail("CODEX_THREAD_ID does not match native thread")
    latest_by_turn = {}
    for position, event in desktop:
        turn = event["payload"].get("turn_id")
        if not isinstance(turn, str) or not turn:
            fail("native turn ID missing")
        latest_by_turn[turn] = (position, event)
    common = {"schema": "tackle-observability-telemetry/1", "captured_at": now,
              "source": str(trace), "scope": "session", "run_id": "n/a"}
    selections = [("thread_token_usage", thread, "codex-desktop/thread-snapshot/1", *desktop[-1])]
    selections.extend(("turn_token_usage", thread + "/turn/" + turn,
                       "codex-desktop/turn/1", *latest)
                      for turn, latest in latest_by_turn.items())
    for basis, scope_id, collector, position, event in selections:
        payload = event["payload"]
        if basis not in payload:
            continue
        turn = payload["turn_id"]
        context = next((item.get("payload", {}) for item in reversed(events[:position])
                        if item.get("type") == "turn_context"
                        and item.get("payload", {}).get("turn_id") == turn), {})
        terminal_event = next((item for item in reversed(events[position + 1:])
                               if item.get("type") == "event_msg"
                               and item.get("payload", {}).get("type") == "task_complete"
                               and item.get("payload", {}).get("turn_id") == turn), None)
        terminal = terminal_event.get("timestamp", "n/a") if terminal_event else "n/a"
        records.append(dict(common, collector=collector, scope_id=scope_id,
                            metrics=metrics(payload[basis]), provenance={
                                "event_type": "token_usage_record", "event_sha256": digest(event),
                                "event_at": event.get("timestamp", "n/a"), "usage_basis": basis,
                                "turn_id": turn, "response_id": payload.get("response_id", "n/a"),
                                "model_configured": context.get("model", "n/a"),
                                "effort_configured": context.get("effort", "n/a"),
                                "terminal_event_at": terminal,
                                "terminal_event_sha256": digest(terminal_event) if terminal_event else "n/a"}))
elif cli:
    threads = {event.get("thread_id") for event in events
               if event.get("type") == "thread.started"}
    if len(threads) != 1 or not next(iter(threads)):
        fail("CLI native thread ID missing or ambiguous")
    thread = next(iter(threads))
    for ordinal, event in enumerate(cli, 1):
        records.append({"schema": "tackle-observability-telemetry/1", "captured_at": now,
                        "collector": "codex-cli/completed-turn/1", "source": str(trace),
                        "scope": "session", "scope_id": thread + "/turn/" + str(ordinal),
                        "run_id": "n/a", "metrics": metrics(event.get("usage")),
                        "provenance": {"event_type": "turn.completed",
                                       "event_sha256": digest(event), "turn_ordinal": ordinal,
                                       "event_at": event.get("timestamp", "n/a")}})
else:
    fail("no completed native usage observation")
if not records:
    fail("native token fields unavailable")

sidecar = workspace / ("resource-usage.telemetry.jsonl" if ledger.name == "resource-usage.md" else "usage.telemetry.jsonl")
if ledger.name == "resource-usage.md" and (workspace / "usage.telemetry.jsonl").exists():
    fail("mixed usage telemetry paths")
if sidecar.is_symlink():
    fail("sidecar symlink rejected")
known = set()
if sidecar.exists():
    try:
        for line in sidecar.read_text().splitlines():
            if line.strip():
                saved = json.loads(line)
                if (not isinstance(saved, dict)
                        or saved.get("schema") != "tackle-observability-telemetry/1"
                        or not isinstance(saved.get("provenance"), dict)):
                    fail("existing sidecar is malformed")
                known.add((saved.get("collector"), saved.get("scope_id"),
                           saved["provenance"].get("event_sha256"),
                           saved["provenance"].get("terminal_event_at", "n/a")))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("existing sidecar is unreadable or malformed")
new = [record for record in records if (record["collector"], record["scope_id"],
       record["provenance"]["event_sha256"],
       record["provenance"].get("terminal_event_at", "n/a")) not in known]
if new:
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(sidecar, flags, 0o600)
    with os.fdopen(fd, "a") as output:
        for record in new:
            output.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
receipt = {"source": str(trace), "observations_added": len(new),
           "scope_ids": [record["scope_id"] for record in records],
           "model_configured": records[0]["provenance"].get("model_configured", "n/a"),
           "effort_configured": records[0]["provenance"].get("effort_configured", "n/a"),
           "terminal_event_at": records[0]["provenance"].get("terminal_event_at", "n/a")}
print(json.dumps(receipt, ensure_ascii=False))
```
<!-- codex-usage-recipe:end -->

Store the receipt in the role's verification record and cite it from the resource usage ledger Source. Keep
missing metrics `n/a`; the sidecar records available fields only. Capture after the native
terminal event from another actor or next turn if the current executor cannot observe its own
future close. This optional recipe does not replace native raw evidence or the ordinary
lifecycle start/finish rows.
