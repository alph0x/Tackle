"""Validation and derived values for a release configuration."""
import json
from pathlib import Path


def load(path):
    data = json.loads(Path(path).read_text())

    def obj(value, fields, where):
        if type(value) is not dict:
            raise ValueError(f'{where}: expected object')
        for key, check in fields.items():
            if key not in value:
                raise ValueError(f'{where}.{key}: missing required key')
            check(value[key], f'{where}.{key}')

    def scalar(kind):
        def check(value, where):
            if type(value) is not kind:
                raise ValueError(f'{where}: expected {kind.__name__}')
        return check

    string, integer = scalar(str), scalar(int)
    def sequence(item, length=None):
        def check(value, where):
            if type(value) is not list or (length is not None and len(value) != length):
                raise ValueError(f'{where}: expected list' + (f' of length {length}' if length else ''))
            for i, v in enumerate(value):
                item(v, f'{where}[{i}]')
        return check
    def nested(fields):
        return lambda value, where: obj(value, fields, where)
    runtime = nested({'path': string, 'version': sequence(integer, 3)})
    claim = nested({k: string for k in ('source', 'section', 'unit', 'kind', 'reason')})
    obj(data, {'schema': string, 'version': string, 'from_version': string, 'base': string,
               'branch': string, 'catalog_revision': sequence(integer, 2),
               'runtimes': nested({'py310': runtime, 'py314': runtime}), 'workspace': string,
               'initiative': string, 'changelog': nested({'path': string, 'sha256': string}),
               'record': nested({'path': string, 'sha256': string, 'destination': string}),
               'claims': sequence(claim), 'parts': sequence(string), 'install_count': integer,
               'expected_ledger_gate': string, 'expected_sweep': string,
               'gating_workspaces': sequence(string)}, 'config')
    if data['schema'] != 'tackle-release/1':
        raise ValueError('config.schema: expected tackle-release/1')
    valid = ['format', 'stamp', 'changelog', 'migrate', 'readme']
    if data['parts'] != [p for p in valid if p in data['parts']]:
        raise ValueError('config.parts: expected ordered subset of release parts')
    return data


def titles(config):
    v = config['version']
    return {'format': 'Format the unit dispositions file', 'stamp': f'Stamp Tackle {v}',
            'changelog': f'Record the Tackle {v} changes',
            'migrate': f'Target the migration catalog at Tackle {v}',
            'readme': f'Point the README at Tackle {v}'}


def runtime_ok(config, label, observed):
    return tuple(observed) == tuple(config['runtimes'][label]['version'])
