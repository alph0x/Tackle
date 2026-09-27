"""Census: bucket every local workspace under --plans, and chain the gating set (a workspace with an
active data row per lint row 8's definition, plus every workspace --gate names) through the
migration steps to /5 on scratch copies under --out. Every other workspace's chain result (clean,
residue, or a named refusal) is recorded but does not gate.

Not a test_*.py file: eval/run_suites.py's registry never discovers it, and it is never run in
CI. Usage:

    python3 eval/migration/census.py --plans docs/plans --out <scratch> \\
        --record <plans-workspace>/verification-records/<task>/census \\
        --held-out '<regex>' --gate <name>

Writes only under --out (disposable scratch copies) and --record (the JSON report); every real
workspace under --plans is read, hashed before and after, and never modified -- an assertion fails
loudly if a copy step or a bug ever touched the source.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECIPES = HERE.parent.parent / 'references/recipes/migrate'


def load_block(path, namespace=None):
    text = path.read_text(encoding='utf-8')
    block = text.split('```python\n', 1)[1].split('\n```', 1)[0]
    ns = dict(namespace or {})
    ns['__name__'] = 'tackle_census_' + path.stem.replace('-', '_')
    exec(compile(block, str(path), 'exec'), ns)
    return ns


SCHEMA = load_block(RECIPES / 'schema.md')
STEP_PRE3_TO_3 = load_block(RECIPES / 'step-pre3-to-3.md', SCHEMA)
STEP_3_TO_4 = load_block(RECIPES / 'step-3-to-4.md', SCHEMA)
STEP_4_TO_5 = load_block(RECIPES / 'step-4-to-5.md', SCHEMA)
CHAIN = {
    'pre-3': (STEP_PRE3_TO_3, '3'),
    '3': (STEP_3_TO_4, '4'),
    '4': (STEP_4_TO_5, '5'),
}
ACTIVE_TOKENS = ('In progress', 'Checking', 'Interrupted', 'Waiting on owner', '\U0001F7E1')


def held_out(relative_path, held_out_re):
    """Excluded from every copy and read this script makes -- census buckets and chains workspaces by
    their board/plan files only, and never had a reason to touch a held-out record; the exclusion just
    makes that true of the bytes too, not only the logic. --held-out sets the pattern; there is no
    default, so a run that omits it fails loudly rather than reading records it should not."""
    return bool(held_out_re.search(relative_path))


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def load_files(directory, held_out_re):
    return {str(p.relative_to(directory)).replace('\\', '/'): p.read_bytes()
            for p in directory.rglob('*') if p.is_file()
            and not held_out(str(p.relative_to(directory)).replace('\\', '/'), held_out_re)}


def hash_all(directory, held_out_re):
    return {path: sha256_bytes(data) for path, data in load_files(directory, held_out_re).items()}


def copytree_excluding_held_out(source, destination, held_out_re):
    def ignore(current, names):
        relative = Path(current).resolve().relative_to(source.resolve())
        return [name for name in names
                if held_out(str((relative / name)).replace('\\', '/'), held_out_re)]
    shutil.copytree(source, destination, symlinks=True, ignore=ignore)


def is_active(files):
    """Lint row 8's definition: a board data row whose trimmed Status is In progress, Checking,
    Interrupted or Waiting on owner (English: it counts because it holds its write
    scope), or the legacy in-progress glyph. The legend line never counts (D-11)."""
    root = SCHEMA['root_files'](files)
    for name in ('task-board.md', 'board.md'):
        if name not in root:
            continue
        try:
            _, _, header, rows = SCHEMA['parse_board'](SCHEMA['decode'](root[name]))
        except ValueError as exc:
            if str(exc) == 'unclosed fenced example':
                return True
            continue
        status_col = SCHEMA['column_index'](header, 'Status')
        if status_col is None:
            continue
        for _, cells in rows:
            if not cells or not re.fullmatch(SCHEMA['ID_RE'], cells[0]):
                continue
            if len(cells) > status_col and cells[status_col] in ACTIVE_TOKENS:
                return True
    return False


def context_for(bucket_target, run_id):
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    methodology = 'Tackle 9.0.0' if bucket_target == '5' else 'Tackle 8.4.0'
    return {'date': date, 'run_id': run_id, 'methodology': methodology}


def chain_workspace(files, run_id):
    """Run every applicable step until detection reaches a terminal bucket (5, lite or unknown), a
    step's transform refuses, or a step's verify reports an error. Never raises.

    Advances through `schema.adopt()`, never `transform()` directly: `transform` requires its `files`
    to already exclude `legacy-*/` (a real workspace this tool scans may already carry one, e.g. this
    initiative's `legacy-8.3/`), and only `adopt()` supplies that, reassembling the result with every
    pre-existing `legacy-*/` directory preserved plus this step's own snapshot. `originals_ok` is an
    independent check of that same guarantee (byte comparison, not trust in `adopt()`'s own return),
    so a regression there is caught here too, not only where it is implemented."""
    current = files
    errors, residue = [], []
    originals_ok = True
    while True:
        try:
            bucket = SCHEMA['schema_of'](current)
        except ValueError as exc:
            return 'unknown', errors, residue, str(exc), originals_ok
        if bucket not in CHAIN:
            return bucket, errors, residue, None, originals_ok
        step, target = CHAIN[bucket]
        context = context_for(target, run_id)
        before_scoped = SCHEMA['workspace_files'](current)
        pre_existing_legacy = {path: data for path, data in current.items() if SCHEMA['is_legacy_path'](path)}
        try:
            adopted, _ = SCHEMA['adopt'](current, context, step['transform'])
        except ValueError as exc:
            return bucket, errors, residue, str(exc), originals_ok
        after_scoped = SCHEMA['workspace_files'](adopted)
        result = step['verify'](before_scoped, after_scoped)
        errors.extend(result['errors'])
        residue.extend(result['residue'])
        for path, data in pre_existing_legacy.items():
            if adopted.get(path) != data:
                originals_ok = False
                errors.append('legacy directory not preserved byte-identical: ' + path)
        prefix = 'legacy-%s/' % bucket
        for path, data in before_scoped.items():
            if adopted.get(prefix + path) != data:
                originals_ok = False
                errors.append('missing or altered legacy snapshot: ' + prefix + path)
        if result['errors']:
            return SCHEMA['schema_of'](after_scoped), errors, residue, None, originals_ok
        current = adopted


def census(plans_dir, out_dir, record_dir, gate_names, held_out_re):
    """Read-only over `plans_dir`: the only writes this function makes are `shutil.copytree` into
    `out_dir` and (by the caller) the JSON report into `record_dir` -- never back into `plans_dir`,
    by construction (there is no other call that takes a path under `plans_dir` as a write target).
    The before/after hash comparison below is a second, independent check of the same property, but
    an active workspace can be edited by a concurrent session between the two snapshots (this
    initiative's own workspace is real and shared); a mismatch there is reported, not raised, and
    named so it is never mistaken for evidence that this function wrote to it."""
    out_dir.mkdir(parents=True, exist_ok=True)
    record_dir.mkdir(parents=True, exist_ok=True)
    rows, counts, concurrent_edits = [], {}, []
    for workspace in sorted(path for path in plans_dir.glob('*') if path.is_dir()):
        name = workspace.name
        before = hash_all(workspace, held_out_re)
        scratch = out_dir / name
        if scratch.exists():
            shutil.rmtree(scratch)
        # symlinks=True (inside the helper): some verification-record stores alias a content-
        # addressed object pool through a `blobs` symlink (references/guides/full-checks.md's
        # capture recipe); copy the link itself, never dereference it (a dereferencing copy can also
        # fail outright on a relative link whose target only resolves from the original directory
        # depth). held-out records are skipped entirely, not merely unread.
        copytree_excluding_held_out(workspace, scratch, held_out_re)
        files = load_files(scratch, held_out_re)
        try:
            bucket = SCHEMA['schema_of'](files)
        except ValueError:
            bucket = 'unknown'
        active = is_active(files)
        gates = active or name in gate_names
        final_bucket, errors, residue, refusal, originals_ok = chain_workspace(files, 'census-' + name)
        rows.append(dict(workspace=name, bucket=bucket, active=active, gates=gates,
                          final_bucket=final_bucket, errors=errors, residue=residue, refusal=refusal,
                          originals_ok=originals_ok))
        counts[bucket] = counts.get(bucket, 0) + 1
        after = hash_all(workspace, held_out_re)
        if before != after:
            if active:
                concurrent_edits.append(name)
            else:
                raise AssertionError('census must never modify a real workspace: ' + name)
    return rows, counts, concurrent_edits


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plans', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--held-out', required=True,
                        help='regex (re.search, on the /-joined relative path) matching a verification '
                             'record to exclude from every copy and read; required, no default')
    parser.add_argument('--gate', action='append', required=True,
                        help='workspace name to gate even if it has no active data row '
                             '(repeatable; required, no default)')
    args = parser.parse_args(argv)
    plans_dir = args.plans.resolve()
    if not plans_dir.is_dir():
        print('no such --plans directory: ' + str(plans_dir), file=sys.stderr)
        return 2
    held_out_re = re.compile(args.held_out)
    rows, counts, concurrent_edits = census(plans_dir, args.out.resolve(), args.record.resolve(), set(args.gate), held_out_re)
    gating = [row for row in rows if row['gates']]
    gating_clean = bool(gating) and all(
        row['final_bucket'] == '5' and not row['errors'] and row['originals_ok'] for row in gating)
    report = dict(schema='tackle-migration-census/1', generated=datetime.now(timezone.utc).isoformat(),
                  plans=str(plans_dir), total=len(rows), counts=counts,
                  gating_set=[row['workspace'] for row in gating], gating_clean=gating_clean,
                  concurrent_edits_during_run=concurrent_edits, rows=rows)
    (args.record.resolve() / 'census.json').write_text(json.dumps(report, indent=2) + '\n')
    print('workspaces:', len(rows))
    print('counts:', counts)
    print('gating set:', [row['workspace'] for row in gating])
    print('gating clean:', gating_clean)
    if concurrent_edits:
        print('note: changed during this run by something other than census.py (active workspace, '
              'not written by this script):', concurrent_edits)
    for row in rows:
        marker = 'GATE' if row['gates'] else '    '
        print('%s %-45s %-8s -> %-8s errors=%d residue=%d originals_ok=%s%s' % (
            marker, row['workspace'], row['bucket'], row['final_bucket'],
            len(row['errors']), len(row['residue']), row['originals_ok'],
            (' refusal=' + row['refusal']) if row['refusal'] else ''))
    return 0 if gating_clean else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
