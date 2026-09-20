# Full — executable observations and bounded closure

Use an equivalent complete harness export when available. Otherwise save this Python 3 recipe
inside the authorized workspace before running checks. This is an optional documentation recipe,
not an installed runner or a new product dependency. This is Full's direct-capture entry from
`run.md` and `evidence-capture.md`; None and Lite keep their own procedures.

## Establish the boundary first

Record allowed writes, protected fixtures and the actual harness policy. Configure native
filesystem restrictions for shell children as well as patch tools; a container protects its host,
not necessarily the Point's Touches inside the container. Put script revisions, evidence and
TMPDIR under authorized paths. TMPDIR routes cooperative tools; it does not prohibit an explicit
`/tmp/name`, a sibling path or a symlink escape. Before the first PLAN write or check, use disposable sentinels to
prove an allowed write succeeds and outside/protected writes are denied. Never probe by changing
a real protected file. Preserve the observed policy and results. If effective confinement is a
required capability and is unavailable, block that scope; do not disable it or claim that an
instruction/audit enforces it. Post-run hashes remain necessary for protected expectations.

## Prepare once, then capture

During PLAN, select a capture destination, exact command and input selectors for each obligation.
Include source, **all selected tests including additive files**, contract, input data, config and
dependencies. Selectors come from the acceptance/check's actual dependency surface, not merely
Point Touches. Review completeness before execution; no generic helper can infer every dynamic
input. A glob records its membership, including an intentionally optional empty match; a required
selector matching nothing is an error. Do not select credentials, home directories or generated
evidence. Save compound scripts before invoking them and include every called script/config;
the recipe automatically includes itself, its JSON specification and existing file arguments after argv[0]. The executable/runtime is
observed separately; absolute interpreter paths are valid. External read-only scripts need an
authorized local snapshot or equivalent harness capture; do not widen write permissions to copy them.
A copied module loaded by an inline interpreter still needs its selector.

The recipe below saves exact input bytes in content-addressed blobs, binary streams and actual
child status. It does not decide whether a shell wrapper's logic is sound. Prefer direct runner
argv; check each required child in compound scripts. A printed PASS or a trailing successful
command must never mask failure. A script correction gets a new observation; previous snapshots
are never replaced. The recipe is for foreground children that join their own children. It cannot
certify process-tree shutdown: on timeout, interrupt or background work, use the harness to stop
all writers and record that confirmation before closing evidence.

Save the block as a workspace-local `capture.py`. Invoke it with one JSON specification path,
for example `python3 docs/plans/demo/capture.py docs/plans/demo/product-check.json`. The JSON has
`argv`, `selectors` (objects with `glob` and `required`), `artifacts` (relative file names),
`destination` (relative directory) and `timeout_seconds`. Use an authorized absolute cwd as the
process cwd; paths resolve from it. For example selectors can cover `src/**/*.py`, `test*.py`,
`SPEC.md`, and the exact validation/config files. Adapt to the real repository, not this example.

```python
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def local(root, name):
    path = root / name
    path.resolve().relative_to(root)
    return path


def select(root, selectors, extra):
    files = set(extra)
    membership = {}
    for item in selectors:
        pattern = item['glob']
        if Path(pattern).is_absolute() or '..' in Path(pattern).parts:
            raise ValueError('selector outside cwd')
        names = sorted(str(p.relative_to(root)) for p in root.glob(pattern) if p.is_file())
        if item['required'] and not names:
            raise ValueError('missing required selector: ' + pattern)
        membership[pattern] = names
        files.update(names)
    data = {name: local(root, name).read_bytes() for name in sorted(files)}
    return membership, data


def capture(spec_path):
    root = Path.cwd().resolve()
    spec_path = local(root, spec_path)
    spec = json.loads(spec_path.read_text())
    argv = spec['argv']
    if not argv or not all(isinstance(x, str) for x in argv):
        raise ValueError('argv must be a nonempty string list')
    extra = [str(spec_path.relative_to(root)), str(Path(__file__).resolve().relative_to(root))]
    for arg in argv[1:]:
        path = Path(arg)
        if (root / path).is_file():
            extra.append(str(local(root, path).relative_to(root)))
    membership, data = select(root, spec['selectors'], extra)
    destination = local(root, spec['destination'])
    destination.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='observation-', dir=destination))
    (out / 'blobs').mkdir()
    def snapshot(payload):
        revisions = {}
        for name, content in payload.items():
            digest = sha(content)
            blob = out / 'blobs' / digest
            if not blob.exists():
                with blob.open('xb') as f:
                    f.write(content)
            revisions[name] = digest
        return revisions
    record = dict(argv=argv, cwd=str(root), capture_runtime=sys.version,
                  actor='n/a', model='n/a', effort='n/a', selectors=spec['selectors'],
                  extra_inputs=extra, membership_before=membership,
                  inputs_before=snapshot(data), timeout_seconds=spec['timeout_seconds'],
                  start=datetime.now(timezone.utc).isoformat())
    def write(name, value):
        with (out / name).open('x') as f:
            json.dump(value, f, indent=2)
    write('start.json', record)
    code, timeout, error = None, False, None
    with (out / 'stdout.bin').open('xb') as stdout, (out / 'stderr.bin').open('xb') as stderr:
        try:
            code = subprocess.run(argv, cwd=root, stdout=stdout, stderr=stderr,
                                  timeout=spec['timeout_seconds']).returncode
        except subprocess.TimeoutExpired:
            timeout = True
        except OSError as exc:
            error = str(exc)
    record.update(end=datetime.now(timezone.utc).isoformat(), child_exit=code,
                  signal=-code if code is not None and code < 0 else None,
                  timeout=timeout, launch_error=error)
    stable, artifacts_present = False, False
    try:
        after_membership, after_data = select(root, spec['selectors'], extra)
        record.update(membership_after=after_membership, inputs_after=snapshot(after_data))
        stable = membership == after_membership and record['inputs_before'] == record['inputs_after']
        record['artifacts'] = snapshot({name: local(root, name).read_bytes() for name in spec['artifacts']})
        artifacts_present = True
    except (OSError, ValueError) as exc:
        record['revision_error'] = str(exc)
    record['streams'] = {name: sha((out / name).read_bytes()) for name in ['stdout.bin', 'stderr.bin']}
    record.update(inputs_stable=stable, artifacts_present=artifacts_present,
                  accepted=code == 0 and not timeout and error is None and stable and artifacts_present)
    write('result.json', record)
    with (out / 'receipt.md').open('x') as f:
        f.write('# Observation\n\n[Actual record](result.json); [start](start.json); '
                '[stdout](stdout.bin); [stderr](stderr.bin).\n\n'
                'Input/artifact bytes are in blobs/<sha256>, mapped by result.json. '
                'Role finish: n/a. Child acceptance is not semantic approval.\n')
    print(out / 'receipt.md')
    return record['accepted']


if __name__ == '__main__':
    raise SystemExit(0 if capture(sys.argv[1]) else 1)
```

Before reusing an observation, open its result and verify stream/blob hashes, relevant final input
hashes **and selector membership**, produced artifacts and the actual accepted child result.
Missing or altered bytes invalidate the observation. A start without a complete result is
incomplete. Retain the old record and run only dependent checks again. Hashes identify bytes;
review of the declared selectors establishes whether those bytes cover the obligation.

## Execute canonical lint faithfully

Run all 16 rows during PLAN before Ready. Read the current `lint-spec.md`; extract the literal
command cell of each numbered row, respecting its backtick delimiter (some use two or four), and
substitute only a validated single-component slug (`[a-z0-9][a-z0-9.-]*`). Save the canonical source snapshot/hash,
row number, command bytes and pass condition. Reject missing/duplicate rows, malformed cells and
an unexpected source revision. Do not invent an equivalent short validator, replace a row with
`true`, or paste the table into an interpolated shell string. Execute each saved command using
`['sh', saved_script]`; retain a separate raw observation for each row. The snapshot of the saved
script must match the extracted bytes. A script's trailing `printf` cannot supply the row result.

For an existing orchestrator, these two pure Python functions provide exact extraction and row
interpretation. Save the extracted UTF-8 bytes verbatim as each script; capture that saved script
with the recipe above. Supply the canonical source hash recorded at preflight, not a hash silently
recomputed after a change. Check that all 16 returned rows are scheduled before initial execution.
Each result carries `row`, `command_sha256`, `source_sha256`, raw observation path and verdict;
build the index from those records. Equivalent harness automation is valid.

Use the connected path below when equivalent harness automation is absent: save this second
block as workspace-local `lint.py` beside `capture.py`, then run `python3 <lint.py> <lint.json>`.
The JSON specifies `source` (current lint-spec path), preflight `source_sha256`, `slug`,
`capture_script`, `selectors`, `destination` and `timeout_seconds`. Optional `rows` selects
affected checks; omission runs all 16. Initial PLAN still requires all 16. Include citation targets
and other actual dependencies in selectors. An authorized read-only source outside cwd is read
and hash-verified, then snapshotted locally; helpers and outputs remain inside cwd. The recipe extracts, saves, captures and verifies
each command itself; do not manually transcribe command cells into another script. A custom
composition remains possible, but compare its actual captured script bytes with the extracted
canonical bytes before claiming canonical coverage. A source/command mismatch or absent script
snapshot is ERROR even if the command exited zero. A subset score is never a full-plan approval.

```python
import hashlib
import re
from pathlib import Path
import json
import subprocess
import sys
import tempfile


def canonical_rows(source, expected_sha256, slug):
    if hashlib.sha256(source).hexdigest() != expected_sha256:
        raise ValueError('canonical source revision changed')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]*', slug):
        raise ValueError('invalid slug')
    rows = {}
    for line in source.decode('utf-8').splitlines():
        if not re.match(r'^\| [0-9]+ ·', line):
            continue
        head, cell, condition = line.split(' | ', 2)
        number = int(head.split(' ·', 1)[0][2:])
        match = re.fullmatch(r'(`+)(.*?)\1', cell)
        if number in rows or not match or not condition.endswith(' |'):
            raise ValueError('duplicate or malformed row')
        command = match[2]
        # Markdown code spans with padding remove one surrounding space.
        if command.startswith(' ') and command.endswith(' ') and command.strip():
            command = command[1:-1]
        command = command.replace('<slug>', slug).encode('utf-8')
        rows[number] = dict(command=command, condition=condition[:-2],
                            command_sha256=hashlib.sha256(command).hexdigest())
    if sorted(rows) != list(range(1, 17)):
        raise ValueError('expected exactly rows 1 through 16')
    return rows


def lint_verdict(row, record, stdout, stderr):
    if row not in range(1, 17):
        raise ValueError('unknown row')
    code = record['child_exit']
    allowed = (0, 1) if row in (5, 6, 11, 15, 16) else (0,)
    if (record['timeout'] or record['launch_error'] or record['signal'] is not None
            or stderr or code not in allowed or not record['inputs_stable']
            or not record['artifacts_present']):
        return 'ERROR'
    if stdout:
        return 'WARN' if row in (8, 13, 15) else 'FAIL'
    if (row == 5 and code != 1) or (row != 5 and row != 15 and code != 0):
        return 'ERROR'
    return 'PASS'


def captured_lint_verdict(source, expected_sha256, slug, row, script, record, observation):
    try:
        expected = canonical_rows(source, expected_sha256, slug)[row]['command']
        if record['argv'] != ['sh', script]:
            return 'ERROR'
        digest = record['inputs_before'][script]
        if not re.fullmatch(r'[0-9a-f]{64}', digest) or record['inputs_after'][script] != digest:
            return 'ERROR'
        actual = (observation / 'blobs' / digest).read_bytes()
        if hashlib.sha256(actual).hexdigest() != digest or actual not in (expected, expected + b'\n'):
            return 'ERROR'
        streams = [(observation / name).read_bytes() for name in ['stdout.bin', 'stderr.bin']]
        for name, data in zip(['stdout.bin', 'stderr.bin'], streams):
            if hashlib.sha256(data).hexdigest() != record['streams'][name]:
                return 'ERROR'
        return lint_verdict(row, record, *streams)
    except (KeyError, OSError, ValueError, TypeError):
        return 'ERROR'


def run_lint(config_path):
    root = Path.cwd().resolve()
    def local(name):
        path = (root / name).resolve()
        path.relative_to(root)
        return path
    config = json.loads(local(config_path).read_text())
    source = Path(config['source']).read_bytes()
    rows = canonical_rows(source, config['source_sha256'], config['slug'])
    selected = config.get('rows', list(rows))
    if not selected or len(set(selected)) != len(selected) or any(n not in rows for n in selected):
        raise ValueError('invalid selected rows')
    destination = local(config['destination'])
    destination.mkdir(parents=True, exist_ok=True)
    batch = Path(tempfile.mkdtemp(prefix='lint-', dir=destination))
    (batch / 'lint-spec.md').write_bytes(source)
    selectors = list(config['selectors'])
    for path in [config_path, batch / 'lint-spec.md', __file__, config['capture_script']]:
        selectors.append(dict(glob=str(local(path).relative_to(root)), required=True))
    results = {}
    for number in selected:
        script_path = batch / ('row-%02d.sh' % number)
        script_path.write_bytes(rows[number]['command'])
        script = str(script_path.relative_to(root))
        spec = dict(argv=['sh', script], selectors=selectors, artifacts=[],
                    destination=str((batch / ('row-%02d' % number)).relative_to(root)),
                    timeout_seconds=config['timeout_seconds'])
        spec_path = batch / ('row-%02d.json' % number)
        spec_path.write_text(json.dumps(spec, indent=2))
        result = subprocess.run([sys.executable, str(local(config['capture_script'])), str(spec_path)],
                                cwd=root, capture_output=True)
        (batch / ('capture-%02d.stdout' % number)).write_bytes(result.stdout)
        (batch / ('capture-%02d.stderr' % number)).write_bytes(result.stderr)
        observation = None
        verdict = 'ERROR'
        try:
            if not result.stdout.strip():
                raise ValueError('missing capture receipt')
            receipt = local(result.stdout.decode().strip())
            receipt.relative_to(batch)
            observation = receipt.parent
            record = json.loads((observation / 'result.json').read_text())
            if result.returncode in (0, 1) and not result.stderr:
                verdict = captured_lint_verdict(source, config['source_sha256'], config['slug'],
                                               number, script, record, observation)
        except (OSError, ValueError, UnicodeError):
            pass
        results[number] = dict(row=number, source_sha256=config['source_sha256'],
                               command_sha256=rows[number]['command_sha256'], verdict=verdict,
                               capture_exit=result.returncode,
                               observation=str(observation.relative_to(root)) if observation else None)
    summary = dict(rows=results, total=len(results),
                   passed=sum(r['verdict'] == 'PASS' for r in results.values()),
                   complete=len(results) == 16 and all(r['verdict'] in ('PASS', 'WARN') for r in results.values()))
    summary_path = batch / 'summary.json'
    summary_path.write_text(json.dumps(summary, indent=2))
    print(summary_path)
    return all(r['verdict'] in ('PASS', 'WARN') for r in results.values())


if __name__ == '__main__':
    raise SystemExit(0 if run_lint(sys.argv[1]) else 1)
```

Interpret **stdout, stderr and real exit together** using the canonical condition:

| Rows | Empty-output pass | Findings | Execution error |
|---|---|---|---|
| 5 | stdout/stderr empty, exit 1 | stdout with grep exit 0: FAIL | stderr, timeout, signal or other exit: ERROR |
| 15 | stdout/stderr empty, exit 0 or 1 | stdout: WARN if exit 0 or 1 and no stderr | stderr, timeout, signal or other exit: ERROR |
| 8, 13 | stdout/stderr empty, exit 0 | stdout with exit 0: WARN | stderr, timeout, signal or nonzero exit: ERROR |
| 6, 11, 16 | stdout/stderr empty, exit 0 | stdout with exit 0 or 1: FAIL | stderr, timeout, signal, unexpected exit or empty-output exit 1: ERROR |
| All other rows | stdout/stderr empty, exit 0 | stdout with exit 0: FAIL | stderr, timeout, signal or nonzero exit: ERROR |

Report every finding verbatim, including findings printed with exit zero. WARN keeps its existing
nonblocking severity; ERROR means the row was not validly observed, never PASS. Preserve failures
and do not let wrapper success certify them. The generic capture recipe's `accepted` means child
exit zero only; lint's row-specific verdict uses its captured fields, not that generic boolean.
The score is computed from these observations, never a constant or a count of launched commands.

## Close against one obligation index

Before RUN, prepare the obligation → command → input selectors → evidence destination mapping,
including required reviews, runtimes, integration/global coverage and packaging. Reuse PLAN's
preparation and canonical lint observations after checking their revisions. After product checks,
write the reports, board/log/usage updates and final output references once, then validate their
affected rows. Link a captured observation from the ledger/report instead of transcribing it.
An observation may satisfy several obligations when its actual coverage does; do not rerun a
passing product suite merely to fill separate target, integration and global headings.

Use this dependency map conservatively when selecting affected lint rows:

| Changed input | Invalidated rows |
|---|---|
| Workspace top-level or one-level Markdown content/membership | 1 |
| Points or plan, including id/dependency membership | 2, 5; Points also 7, 9, 12 |
| Board | 2, 3, 10, 11, 14; every initiative board also 8 |
| Points/plan/reference citations or their target bytes | 4 |
| Log or log-archive content/membership | 6; log also 13 |
| Design contract or decisions | 7 |
| Any initiative's Points/Touches membership/content | 8 |
| Usage membership/content | 11, 16 |
| Closure report membership | 14 |
| Workspace AGENTS | 13, 15 |
| Reference-doc membership/content, current time crossing freshness window | 15 |
| Lint source, command interpreter/tools or policy relevant to its execution | All affected rows; all 16 if impact cannot be established |

Union dependencies; the same edit can match several rows. Track glob membership, citation target
files and time as well as hashes of known files. Do not reuse row 15 without a verified expiry
boundary; rerun this inexpensive row when freshness is uncertain. Unknown dependencies invalidate
the potentially affected observations. Product checks have their own input map.

The final index still accounts for all 16 canonical rows, distinguishing fresh executions from
reused current observations; report `lint: N/16 checks passed` from their actual pass conditions
(and any additional workspace rows in the denominator). This is a current coverage summary;
also report how many rows were executed versus reused. A selection of custom checks is not 16/16.
The release sweep still executes every prescribed row and gate; this reuse rule does not waive it.

Finish with complete only when all mandatory obligations have current accessible evidence.
Otherwise finish with the bounded blocker packet from `run.md`, preserving completed unaffected
work and the unresolved obligation. Budget exhaustion ends with an honest incomplete/blocked
handoff. It does not justify changing acceptance, omitting global coverage or another unbounded
bookkeeping loop. Correct an observed failure within the existing recovery budget; do not restart
unchanged preparation merely because a new heading or session begins.

Explicit Lite applicability uses the first-line marker and shape checks in `lint-spec.md`, not
absence of Full files. Include plan.md in selectors for every row: route changes invalidate all
applicability observations. During release, execute all sixteen commands even for Lite and accept
Full-only checked skips only after row 1 passes. This does not waive selected global acceptance.
