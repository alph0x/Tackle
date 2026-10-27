# Reusable evaluation rounds

This optional local tool seals one finite evaluation round, reserves each unit before its caller performs an effect, and computes or replays the result from retained public observations. It does not dispatch work, inspect opaque cases or answers, qualify an adapter, or establish independent evidence. Use it only when a prepared task has an explicit round protocol and script consent. Ordinary `verify` remains the readiness and finding workflow; this guide is an on-demand depth reference, not an automatic verification step.

The command is `python3 -I skills/tackle/scripts/evaluation_rounds.py`. It uses Python 3.10+ and the standard library. The four operations are `seal --spec spec.json --round round-01`, `record --round round-01 --event event.json`, `compute --round round-01 --output result-01`, and `replay --round round-01 --against result-01/result.json --output replay-01`. Run them from the fixture cwd. A round destination and each result directory must be new, disjoint directories below that cwd. The tool refuses overwrites, symlinks, escapes, changed inputs, malformed evidence, and unsupported schema or rules.

## Finite sealed inputs

A `tackle-round/1` manifest has exactly these top-level fields: `schema`, `round_id`, `hypothesis`, `primary_metric`, `created_at`, `context`, `inputs`, `cases`, `arms`, `strata`, `comparisons`, `order`, `budgets`, `opening`, `qualifications`, and `lineage`. Its canonical UTF-8 JSON is sorted by key, compact, finite, duplicate-free, and ends in one LF. The seal is SHA-256 of those canonical bytes before `seal_sha256` is added. Every operation rechecks the seal and declared public-local file hashes.

`context` records `repo`, `checkout`, `workspace`, `records`, `procedure`, `runtime`, and `binding_reference`. `inputs` use `{id,sha256,kind,path}`; a `public-local` path is a regular file below cwd, while an `opaque` entry has `path:null` and is never opened. Cases reference declared input and opaque oracle IDs. A stratum records capability, effort, support and a declared binding-input ID. A comparison names its baseline and candidate arms and a closed `paired-count/1` rule with positive `n_min`, `win_min` and `defect_reduction_min`; optional limits are integer `max_time_ratio` numerator/denominator and `max_additional_judgment_wait_ms`.

The finite `order` lists unique smoke rows before measurement rows. Each row names `unit_id`, `stage`, `case_id`, `arm`, `stratum`, and a full reservation vector for every declared budget dimension. Episodes is exactly one per row. The initial dimensions are episodes, turns, judgment_requests and wall_ms; optional money is an integer declared currency unit. Seal checks that each comparison/stratum has at least its planned measurement-pair floor. Smoke and one-sided measurement rows never become pairs. There is no sampling, Cartesian expansion, automatic replacement, early favorable stop or pooling across strata.

Calibrate measurement cases before sealing them. Development cases, run at the bound model and effort, must show that the baseline arm fails some of them and that each treatment's trigger occurs (for example, a situation that makes the executor invoke judgment). When every arm solves every development case, or a treatment's trigger never occurs, the round can only tie or measure overhead: stop for an owner decision before any measurement spend instead of sealing it.

`opening` carries exact reserved, known-consumed and unknown vectors, correction count, and either a same-pool parent receipt or a new-allocation receipt. New allocations explicitly carry zero opening state. Inherited state must match the canonical retained parent result; missing knowledge is not zero. `lineage` fixes the budget pool and parent result reference. A child round keeps its parent's exact limits, unless `opening` also carries an optional `extension_receipt` (`{path,sha256}`, the owner's decision): then each limit may equal or exceed the parent's, never fall below it. An extension receipt without a parent result is refused. These identity and arithmetic checks do not prove authorization or receipt truth. Qualification requirements name procedure-input IDs; starts require a passing retained receipt for every requirement. Actors and labels alone do not establish independence.

## Events, reservations and results

Each event has exactly `event_id`, `kind`, `seal_sha256`, `recorded_at`, `actor`, `unit_id`, and `payload`. Kinds are:

- `qualification`: unit is null; payload is `{id,status,receipt}`, with status `pass`, `fail`, or `unavailable`.
- `start`: unit names the next sealed row; payload is `{}`.
- `finish`: payload is `{status,usage,scores,receipt,corrections_delta}`.
- `reconcile`: same terminal fields plus `prior_event_sha256`; it fills only previously unknown facts.
- `stop`: unit is null; payload is `{reason,state,receipt}`, with state `aborted`, `infrastructure-failure`, or `inconclusive`.

Terminal status is `success`, `failed`, `infrastructure-failure`, `aborted`, or `unknown`. Usage contains every budget dimension with an integer or null. Scores are null only for unknown status; otherwise they contain boolean correctness, safety (`preserved`, `violated`, or `unknown`), nonnegative defects, wall_ms and additional_judgment_wait_ms (integer or null). Receipt references are `{path,sha256}` for regular files below cwd. The event chain hashes canonical `{sequence,previous_sha256,event}` bytes plus LF; its first predecessor is the seal.

`record` appends one event in a SQLite `BEGIN IMMEDIATE` transaction with timeout zero. It never performs the external action. It commits and closes a start reservation before returning `dispatch_allowed:true`. At most one unit may be active. A duplicate identical event returns its original identity with `dispatch_allowed:false`; a conflicting event, lost acknowledgement, busy store, or unknown result is never permission to repeat an effect. Started reservations are never refunded. Reconcile can resolve only unknown fields and cannot erase known failure, overrun, stop, correction or reservation facts. Compute and replay open the database read-only and do not recover journals or mutate evidence.

A `tackle-round-result/1` result is deterministic for a seal and event head. It contains every required comparison/stratum/case pair, missing and unknown data, relevant smoke/unpaired exclusions, budgets, qualifications, lineage and derived summary. Unknown values remain null; they are never treated as zero, false, complete, or favorable. Required pairs stay required even when the floor is met. A favorable decision needs all declared pairs complete, enough valid pairs, no loss, and either the declared win or defect-reduction threshold. Timing constraints use integer cross multiplication; per-episode judgment wait uses its declared ceiling. Ties, incomplete pairs, failed qualification, and critical uncertainty cannot become support. Infrastructure failure, abort, not-run, running, inconclusive and success follow the sealed state precedence; a successful round can still reject a candidate.

`replay` performs the same fold, writes a fresh result, and compares its canonical bytes to the retained expected result for the same seal and event head. It does not call a model, adapter or subprocess. A match proves only deterministic local replay of the recorded bytes, not their custody, external validity, host confinement, or independent judgment.

To replace a stopped round, seal a new child round: its parent is the stopped round's computed result, its opening carries that result's summary, and any added episode or budget cites the owner's extension receipt. Never edit or reopen the stopped round. Any durable per-unit request-identity store the caller keeps (an admission gate, for example) starts fresh for the child, because the replaced unit's identity is already consumed there.

## Output and limits

Successful operations print one `tackle-round-receipt/1` JSON object. Seal and record operations return zero after successful writes. Compute returns zero only for round state `success`; other valid states return one. Replay returns zero only when bytes match and the round state is `success`; mismatch and non-success return one. Invalid arguments, schema, path, seal, chain or conflicting event return two. A busy or unavailable local store returns three. A printed operation receipt never means candidate acceptance.

The SQLite file is a local append-only interface, not tamper-proof custody. The module contains no transport, callback, model, network access, subprocess, plugin or evaluator import. The installed script remains optional and requires the repository's existing explicit script consent. External qualification, protected inputs, route isolation, observation validity, independent review and held-out safety evidence remain with their declared owners.

## Complete disposable public fixture

Run the block from the installed skill's scripts directory. It resolves that directory's physical path and verifies evaluation_rounds.py is a file before creating or entering the fresh fixture. It needs only the installed artifact and Python's standard library. The public observations below are synthetic fixture data, not calibration, authorization, custody, independent judgment or host qualification. Running the example still needs the existing explicit script consent. Nothing here dispatches a model or adapter.

Choose the fresh directory below only if absent. A failed command stops the route; retain its native streams/receipts and inspect them before any repeat. Do not overwrite an existing round, output or fixture. The successful route records an unknown finish, resolves it from retained fixture observation, completes the pair and computes/replays supported. The stop branch is a separately allocated fresh round, so it does not overwrite or stop the successful one. All five event kinds are constructed explicitly.

```sh
set -eu
TOOL="$(pwd -P)/evaluation_rounds.py"
test -f "$TOOL"
mkdir /tmp/tackle-round-guide-fixture
cd /tmp/tackle-round-guide-fixture
python3 -I - <<'PY'
from pathlib import Path
import hashlib, json
root = Path.cwd().resolve()
def put(name, value):
    path = root / name
    path.write_bytes((json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8"))
    return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
(root / "retained").mkdir()
public = put("public.json", {"fixture": "public metadata only"})
allocation = put("allocation.json", {"fixture_allocation": "normal round only"})
stop_allocation = put("stop-allocation.json", {"fixture_allocation": "stop round only"})
put("observation.json", {"fixture_observation": "synthetic, not qualification evidence"})
dims = ("episodes", "turns", "judgment_requests", "wall_ms")
reservation = dict(episodes=1, turns=20, judgment_requests=2, wall_ms=60000)
value = dict(
    schema="tackle-round/1", round_id="public-example", hypothesis="public paired fixture",
    primary_metric="correctness", created_at="2026-10-22T00:00:00Z",
    context=dict(repo=str(root), checkout=str(root), workspace=str(root), records=str(root / "retained"),
                 procedure="public-fixture", runtime="python-stdlib", binding_reference="fixture"),
    inputs=[dict(id="fixture", kind="public-local", **public),
            dict(id="opaque-oracle", kind="opaque", path=None,
                 sha256=hashlib.sha256(b"public opaque identity, not answers").hexdigest())],
    cases=[dict(case_id="x1", input_id="fixture", oracle_id="opaque-oracle")], arms=["A", "B"],
    strata=[dict(id="low", capability="low", effort="low", support="supported", binding_input_id="fixture")],
    comparisons=[dict(id="B/A", baseline_arm="A", candidate_arm="B",
                      decision_rule=dict(name="paired-count/1", n_min=1, win_min=1, defect_reduction_min=2))],
    order=[dict(unit_id="x1-" + arm, stage="measurement", case_id="x1", arm=arm, stratum="low",
                reservation=dict(reservation)) for arm in ("A", "B")],
    budgets={key: dict(unit=key, limit=2 * reservation[key]) for key in dims},
    opening=dict(reserved={key: 0 for key in dims}, known_consumed={key: 0 for key in dims},
                 unknown={key: 0 for key in dims}, corrections=0, parent_receipt=None,
                 new_allocation_receipt=allocation),
    qualifications=[dict(id="instrument", procedure_input_id="fixture")],
    lineage=dict(budget_pool_id="public-example-pool", parent_result=None))
put("spec.json", value)
value["round_id"] = "public-stop-example"
value["lineage"]["budget_pool_id"] = "public-stop-pool"
value["opening"]["new_allocation_receipt"] = stop_allocation
put("spec-stop.json", value)
PY
python3 -I "$TOOL" seal --spec spec.json --round round-01 > seal.receipt.json
python3 -I - <<'PY'
from pathlib import Path
import hashlib, json
root = Path.cwd()
seal = json.loads((root / "round-01/manifest.json").read_bytes())["seal_sha256"]
observation = {"path": "observation.json", "sha256": hashlib.sha256((root / "observation.json").read_bytes()).hexdigest()}
def event(name, kind, unit, payload):
    value = dict(event_id=name, kind=kind, seal_sha256=seal, recorded_at="2026-10-22T00:00:00Z",
                 actor="public-fixture-controller", unit_id=unit, payload=payload)
    (root / (name + ".json")).write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
event("qualification", "qualification", None, dict(id="instrument", status="pass", receipt=observation))
event("start-a", "start", "x1-A", {})
event("unknown-a", "finish", "x1-A", dict(status="unknown",
      usage=dict(episodes=None, turns=None, judgment_requests=None, wall_ms=None),
      scores=None, receipt=observation, corrections_delta=1))
event("start-b", "start", "x1-B", {})
event("finish-b", "finish", "x1-B", dict(status="success",
      usage=dict(episodes=1, turns=5, judgment_requests=0, wall_ms=100),
      scores=dict(correct=True, safety="preserved", defects=0, wall_ms=100, additional_judgment_wait_ms=0),
      receipt=observation, corrections_delta=0))
PY
python3 -I "$TOOL" record --round round-01 --event qualification.json > qualification.receipt.json
python3 -I "$TOOL" record --round round-01 --event start-a.json > start-a.receipt.json
python3 -I "$TOOL" record --round round-01 --event unknown-a.json > unknown-a.receipt.json
python3 -I - <<'PY'
from pathlib import Path
import json
root = Path.cwd()
previous = json.loads((root / "unknown-a.receipt.json").read_bytes())["event_sha256"]
value = json.loads((root / "unknown-a.json").read_bytes())
value.update(event_id="resolve-a", kind="reconcile")
value["payload"].update(status="success", corrections_delta=0, prior_event_sha256=previous,
    usage=dict(episodes=1, turns=5, judgment_requests=0, wall_ms=100),
    scores=dict(correct=False, safety="preserved", defects=0, wall_ms=100, additional_judgment_wait_ms=0))
(root / "resolve-a.json").write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
PY
python3 -I "$TOOL" record --round round-01 --event resolve-a.json > resolve-a.receipt.json
python3 -I "$TOOL" record --round round-01 --event start-b.json > start-b.receipt.json
python3 -I "$TOOL" record --round round-01 --event finish-b.json > finish-b.receipt.json
python3 -I "$TOOL" compute --round round-01 --output result-01 > compute.receipt.json
python3 -I "$TOOL" replay --round round-01 --against result-01/result.json --output replay-01 > replay.receipt.json
python3 -I "$TOOL" seal --spec spec-stop.json --round round-stop > stop-seal.receipt.json
python3 -I - <<'PY'
from pathlib import Path
import hashlib, json
root = Path.cwd()
value = dict(event_id="explicit-stop", kind="stop",
    seal_sha256=json.loads((root / "round-stop/manifest.json").read_bytes())["seal_sha256"],
    recorded_at="2026-10-22T00:00:00Z", actor="public-fixture-controller", unit_id=None,
    payload=dict(reason="public-fixture-stop", state="aborted",
                 receipt=dict(path="observation.json", sha256=hashlib.sha256((root / "observation.json").read_bytes()).hexdigest())))
(root / "stop.json").write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
PY
python3 -I "$TOOL" record --round round-stop --event stop.json > stop.receipt.json
code=0
python3 -I "$TOOL" compute --round round-stop --output stopped-result > stopped-compute.receipt.json || code=$?
test "$code" -eq 1
code=0
python3 -I "$TOOL" replay --round round-stop --against stopped-result/result.json --output stopped-replay > stopped-replay.receipt.json || code=$?
test "$code" -eq 1
```

The normal result is one complete pair, W1/L0/supported, reserved episodes2, remaining episodes0 and corrections1. Its replay matches canonical result bytes without another effect. The stop branch retains its explicit aborted state and uses zero episode reservations; matching replay still returns one because the round is not success. Inspect actual receipts/results and native exits; these declared fixture expectations are not observed runtime evidence. No unknown consumption is inferred as zero, and opaque bytes are never provided/opened. Retain the complete fixture and raw native streams when an authorized controller qualifies this example; do not delete uncertain evidence or treat the example as permission to run a real cohort.
