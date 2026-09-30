"""Conservative family selection; the full registry is validated by the runner."""
import fnmatch
import json
from pathlib import PurePosixPath


def changed_path(value):
    if not value or any(c in value for c in ('\x00', '\n', '\r', '\\')):
        raise ValueError('invalid repository-relative changed path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('changed path must stay inside the repository: ' + value)
    return str(path)


def select(root, manifest, changed, phase):
    if phase not in ('development', 'integration', 'release'):
        raise ValueError('unknown selection phase: ' + phase)
    families = [s['path'] for s in manifest['suites']]
    paths = sorted({changed_path(p) for p in changed or []})
    reasons = {f: [] for f in families}
    unknown = []

    def include(names, path, why):
        for name in names:
            if name not in reasons:
                raise ValueError('selection names unregistered family: ' + name)
            reasons[name].append({'changed': path, 'reason': why})

    if changed is None or phase != 'development':
        include(families, None, 'complete registry: default, integration or release')
    else:
        mapping = json.loads((root / 'eval/check-selection.json').read_text())
        if mapping.get('version') != 1 or len(mapping['families']) != len(families) or set(mapping['families']) != set(families):
            raise ValueError('selection families differ from full registry; review the dependency map')
        for rule in mapping['rules']:
            if set(rule['families']) - set(families):
                raise ValueError('selection names unregistered family')
        if set(mapping['test_source_regressions']) - set(families):
            raise ValueError('selection names unregistered regression family')
        for path in paths:
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
                registered_tests=sum(s['tests'] for s in manifest['suites']))
