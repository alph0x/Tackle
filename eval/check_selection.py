"""Conservative family selection; the full registry is validated by the runner."""
import fnmatch
import json
from pathlib import PurePosixPath

MANIFEST_PATH = 'eval/suite-manifest.json'


def changed_path(value):
    if not value or any(c in value for c in ('\x00', '\n', '\r', '\\')):
        raise ValueError('invalid repository-relative changed path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('changed path must stay inside the repository: ' + value)
    return str(path)


def json_semantically_equal(left, right):
    if isinstance(left, dict) or isinstance(right, dict):
        return (isinstance(left, dict) and isinstance(right, dict)
                and left.keys() == right.keys()
                and all(json_semantically_equal(left[key], right[key]) for key in left))
    if isinstance(left, list) or isinstance(right, list):
        return (isinstance(left, list) and isinstance(right, list)
                and len(left) == len(right)
                and all(json_semantically_equal(a, b) for a, b in zip(left, right)))
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left is right
    if isinstance(left, (int, float)) or isinstance(right, (int, float)):
        return (isinstance(left, (int, float)) and not isinstance(left, bool)
                and isinstance(right, (int, float)) and not isinstance(right, bool)
                and left == right)
    return type(left) is type(right) and left == right


def validate_baseline(manifest):
    if not isinstance(manifest, dict) or not json_semantically_equal(manifest.get('version'), 1):
        raise ValueError('manifest baseline must be a version 1 object')
    suites = manifest.get('suites')
    if not isinstance(suites, list) or not suites:
        raise ValueError('manifest baseline needs a nonempty suite list')
    paths = set()
    for suite in suites:
        if not isinstance(suite, dict):
            raise ValueError('manifest baseline suite rows must be objects')
        path = suite.get('path')
        if not isinstance(path, str):
            raise ValueError('manifest baseline suite path must be text')
        try:
            normalized = changed_path(path)
        except ValueError as error:
            raise ValueError('manifest baseline suite path must stay inside eval: ' + path) from error
        parts = PurePosixPath(normalized)
        if parts.parts[0] != 'eval' or normalized != path:
            raise ValueError('manifest baseline suite path must stay inside eval: ' + path)
        if path in paths:
            raise ValueError('manifest baseline has duplicate suite: ' + path)
        paths.add(path)
        files = suite.get('files')
        if not isinstance(files, list) or not files:
            raise ValueError('manifest baseline suite needs explicit files: ' + path)
        if any(not isinstance(name, str) or PurePosixPath(name).name != name
               or not name.startswith('test_') or not name.endswith('.py') for name in files):
            raise ValueError('manifest baseline has invalid test filename: ' + path)
        if len(set(files)) != len(files):
            raise ValueError('manifest baseline has duplicate test filename: ' + path)
        if type(suite.get('tests')) is not int or suite['tests'] <= 0:
            raise ValueError('manifest baseline expected tests must be a positive integer: ' + path)


def classify_manifest(current, baseline):
    validate_baseline(baseline)
    current_by_path = {suite['path']: suite for suite in current['suites']}
    baseline_by_path = {suite['path']: suite for suite in baseline['suites']}
    reasons = []
    current_metadata = {key: value for key, value in current.items() if key != 'suites'}
    baseline_metadata = {key: value for key, value in baseline.items() if key != 'suites'}
    if not json_semantically_equal(current_metadata, baseline_metadata):
        reasons.append('top-level manifest metadata changed')
    if set(current_by_path) != set(baseline_by_path):
        reasons.append('suite family membership changed')
    deltas = []
    for path in sorted(set(current_by_path) & set(baseline_by_path)):
        now, before = current_by_path[path], baseline_by_path[path]
        now_metadata = {key: value for key, value in now.items() if key not in ('path', 'files', 'tests')}
        old_metadata = {key: value for key, value in before.items() if key not in ('path', 'files', 'tests')}
        if not json_semantically_equal(now_metadata, old_metadata):
            reasons.append('suite metadata changed: ' + path)
        current_files, baseline_files = now['files'], before['files']
        current_set, baseline_set = set(current_files), set(baseline_files)
        kinds = []
        if current_set - baseline_set:
            kinds.append('files-added')
        if baseline_set - current_set:
            kinds.append('files-removed')
        if not kinds and current_files != baseline_files:
            kinds.append('files-reordered-only')
        if now['tests'] != before['tests']:
            kinds.append('count-changed')
        deltas.append({'family': path, 'kinds': kinds or ['unchanged'],
                       'files_added': sorted(current_set - baseline_set),
                       'files_removed': sorted(baseline_set - current_set),
                       'count_before': before['tests'], 'count_current': now['tests']})
    qualified = not reasons
    return {'qualified': qualified, 'reason': 'files/count-only delta' if qualified else '; '.join(reasons),
            'families': deltas, 'affected_families': [item['family'] for item in deltas
                if any(kind != 'files-reordered-only' and kind != 'unchanged' for kind in item['kinds'])]}


def select(root, manifest, changed, phase, *, manifest_baseline=None,
           manifest_baseline_path=None, manifest_baseline_sha256=None):
    if phase not in ('development', 'integration', 'release'):
        raise ValueError('unknown selection phase: ' + phase)
    families = [s['path'] for s in manifest['suites']]
    paths = sorted({changed_path(p) for p in changed or []})
    reasons = {f: [] for f in families}
    unknown = []
    if manifest_baseline_path is not None and manifest_baseline is None:
        raise ValueError('manifest baseline must be a version 1 object')
    manifest_impact = {'baseline_supplied': manifest_baseline is not None,
                       'baseline_path': str(manifest_baseline_path) if manifest_baseline_path is not None else None,
                       'baseline_sha256': manifest_baseline_sha256, 'status': 'not-supplied',
                       'reason': 'no explicit manifest baseline'}
    if manifest_baseline is not None:
        validate_baseline(manifest_baseline)
        if changed is None:
            manifest_impact.update(status='unused', reason='default selection is complete')
        elif phase != 'development':
            manifest_impact.update(status='unused', reason='integration and release selection is complete')
        elif MANIFEST_PATH not in paths:
            manifest_impact.update(status='unused', reason='changed set does not contain eval/suite-manifest.json')
        else:
            manifest_impact['classification'] = classify_manifest(manifest, manifest_baseline)
            manifest_impact['status'] = 'qualified' if manifest_impact['classification']['qualified'] else 'unqualified'
            manifest_impact['reason'] = manifest_impact['classification']['reason']

    manifest_reader_families = []
    mapping = None
    if changed is not None and phase == 'development':
        mapping = json.loads((root / 'eval/check-selection.json').read_text())
        if mapping.get('version') != 1 or len(mapping['families']) != len(families) or set(mapping['families']) != set(families):
            raise ValueError('selection families differ from full registry; review the dependency map')
        for rule in mapping['rules']:
            if set(rule['families']) - set(families):
                raise ValueError('selection names unregistered family')
            if any(fnmatch.fnmatchcase(MANIFEST_PATH, pattern) for pattern in rule['patterns']) and not any(
                    fnmatch.fnmatchcase(MANIFEST_PATH, pattern) for pattern in rule.get('exclude', [])):
                manifest_reader_families.extend(rule['families'])
        manifest_reader_families = list(dict.fromkeys(manifest_reader_families))
        manifest_impact['reader_families'] = manifest_reader_families
        if set(mapping['test_source_regressions']) - set(families):
            raise ValueError('selection names unregistered regression family')

    def include(names, path, why):
        for name in names:
            if name not in reasons:
                raise ValueError('selection names unregistered family: ' + name)
            reasons[name].append({'changed': path, 'reason': why})

    if changed is None or phase != 'development':
        include(families, None, 'complete registry: default, integration or release')
    else:
        for path in paths:
            if path == MANIFEST_PATH and manifest_impact['status'] == 'qualified':
                detail = manifest_impact['classification']
                for item in detail['families']:
                    if item['family'] in detail['affected_families']:
                        kinds = ', '.join(item['kinds'])
                        include([item['family']], path, 'manifest delta ' + kinds + ': registered files/count changed')
                include(manifest_reader_families, path, 'manifest readers: registry, product template and planning consumers')
                include(mapping['test_source_regressions'], path, 'discovery/count protection')
                continue
            if any(fnmatch.fnmatchcase(path, p) for p in mapping['ignored_patterns']):
                continue
            if any(fnmatch.fnmatchcase(path, p) for p in mapping['global_patterns']):
                include(families, path, 'global registry/runtime dependency')
                continue
            matched = False
            for suite in manifest['suites']:
                if path.startswith(suite['path'] + '/'):
                    matched = True
                    include([suite['path']], path, 'owned test family')
            for rule in mapping['rules']:
                if any(fnmatch.fnmatchcase(path, p) for p in rule['patterns']) and not any(
                        fnmatch.fnmatchcase(path, p) for p in rule.get('exclude', [])):
                    matched = True
                    include(rule['families'], path, rule['reason'])
            if not matched:
                unknown.append(path)
                include(families, path, 'unmapped path: full registry pending dependency review')
            if PurePosixPath(path).name.startswith('test_') and path.endswith('.py'):
                include(mapping['test_source_regressions'], path, 'discovery/count protection')
    selected = [f for f in families if reasons[f]]
    return dict(phase=phase, changed=paths, selected=selected, reasons={f: reasons[f] for f in selected},
                unknown_paths=unknown, complete=len(selected) == len(families),
                planned_tests=sum(s['tests'] for s in manifest['suites'] if s['path'] in selected),
                registered_tests=sum(s['tests'] for s in manifest['suites']), manifest_impact=manifest_impact)
