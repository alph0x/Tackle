# Executable gate example

Adapt the expected values and command to the task. This example checks evidence captured once from a product command. The validator never writes product files. Its negative tests use independent in-memory evidence, not malformed product inputs or edits to real output. A standalone Python process propagates exceptions as nonzero exit; only its final line prints the gate PASS.

Prerequisites: POSIX shell, Python 3, and the task's command/input in the declared cwd. Replace the demo paths and literals when authoring a briefing. For wrapped commands, populate the evidence from the wrapper's result fields, checking wrapper success separately; never substitute wrapper exit for child exit.

## Fixture isolation

The acceptance gate observes the supplied input and resulting output; it must not reset inputs, delete output directories, or repair evidence before checking. If clean setup is necessary, create a fresh temporary directory and stage only declared fixtures there. Cleanup may remove only that temporary directory. Never delete a caller's preexisting files to make the product pass. Test this boundary with a preexisting sentinel: the validator must preserve it and reject an unexpected output entry when the task requires an exact file set.

## Exact JSON schemas

When the task specifies an exact schema, validate keys and types at every object level before reading values. Check list element schemas, count, unique IDs, allowed values and completeness as required. Python equality alone is insufficient for typed schemas: `False == 0` and `True == 1`. Use `type(value) is int` when booleans are forbidden. Keep observed process evidence separate from parsed JSON; never merge untrusted keys over the observed exit or stdout. Include extra-key and wrong-type negative fixtures as well as wrong values.

When formatting is irrelevant, validate the parsed structure by exact keys, types, and values. Compare input bytes or whitespace/newlines only when the task explicitly specifies an exact byte contract; invented whitespace/newline requirements are invalid.

For example, an exact object with integer `child_exit` and a list `tests` needs `type(result) is dict`, `set(result) == {'child_exit', 'tests'}`, `type(result['child_exit']) is int`, and `type(result['tests']) is list`. Each test object must likewise have exactly the task's keys and types before validating its ID/status. These checks apply only when the task declares that schema; do not invent a schema or product behavior.

## Read-only gate pattern

```sh
cd /tmp/tackle-demo && python3 - <<'PY'
from pathlib import Path
import subprocess

EXPECTED = b'name,score\nBo,3\nAda,2\n'

def validate(evidence):
    if (evidence['exit'] != 0 or evidence['timeout']
            or evidence['signal'] is not None
            or evidence['stdout'] != b'PASS normalize: 2 rows\n'
            or evidence['output'] != EXPECTED):
        raise ValueError('invalid evidence')

def test_validator():
    good = dict(exit=0, timeout=False, signal=None,
                stdout=b'PASS normalize: 2 rows\n', output=EXPECTED)
    validate(good)
    for field, wrong in [('exit', 7), ('timeout', True), ('signal', 15),
                         ('stdout', b'wrong\n'), ('output', b'wrong\n')]:
        bad = {**good, field: wrong}
        try:
            validate(bad)
        except ValueError:
            continue
        raise RuntimeError('validator accepted invalid ' + field)

test_validator()
run = subprocess.run(['python3', 'normalize.py', 'input.csv', 'output.csv'],
                     capture_output=True)
validate(dict(exit=run.returncode, timeout=False, signal=None,
              stdout=run.stdout, output=Path('output.csv').read_bytes()))
print('PASS gate')
PY
```

The task command produces output normally; the validator and its self-tests only read it. Failed product evidence exits nonzero before `PASS gate`. A negative self-test succeeds only when the validator rejects its synthetic evidence. Do not confuse that expected rejection with a failure of the product's acceptance command. Keep stdout newline requirements explicit in the task contract.

## Wrapped command example

For a wrapper, validate the wrapper process and the child evidence as separate observed fields, then validate the generated artifact independently. The validator is read-only; the product command may write its declared artifact. This complete example can be pasted into a POSIX shell with Python 3 and the declared `/tmp/tackle-demo` fixtures:

```sh
cd /tmp/tackle-demo && python3 - <<'PY'
from pathlib import Path
import json
import subprocess

EXPECTED = b'name,score\nBo,3\nAda,2\n'
EXPECTED_RESULT = {'child_exit': 0, 'timed_out': False, 'signal': None,
                  'stdout': 'PASS normalize: 2 rows\n'}

def validate(evidence):
    if type(evidence) is not dict or set(evidence) != {'wrapper_exit', 'wrapper_stdout', 'result', 'output'}:
        raise ValueError('invalid evidence shape')
    if type(evidence['wrapper_exit']) is not int or evidence['wrapper_exit'] != 0:
        raise ValueError('wrapper failed')
    if type(evidence['wrapper_stdout']) is not bytes or evidence['wrapper_stdout'] != b'CAPTURED\n':
        raise ValueError('wrapper stdout mismatch')
    result = evidence['result']
    if type(result) is not dict or set(result) != set(EXPECTED_RESULT):
        raise ValueError('result schema mismatch')
    if type(result['child_exit']) is not int or result['child_exit'] != 0:
        raise ValueError('child exit mismatch')
    if type(result['timed_out']) is not bool or result['timed_out'] is not False:
        raise ValueError('timeout mismatch')
    if result['signal'] is not None and type(result['signal']) is not int:
        raise ValueError('signal type mismatch')
    if result['signal'] is not None:
        raise ValueError('signal mismatch')
    if type(result['stdout']) is not str or result['stdout'] != EXPECTED_RESULT['stdout']:
        raise ValueError('child stdout mismatch')
    if type(evidence['output']) is not bytes or evidence['output'] != EXPECTED:
        raise ValueError('artifact mismatch')

good = {'wrapper_exit': 0, 'wrapper_stdout': b'CAPTURED\n', 'result': dict(EXPECTED_RESULT), 'output': EXPECTED}
validate(good)
for field, wrong in [('wrapper_exit', 2), ('wrapper_stdout', b'wrong\n'),
                     ('result', dict(EXPECTED_RESULT, child_exit=3)),
                     ('result', dict(EXPECTED_RESULT, timed_out=True)),
                     ('result', dict(EXPECTED_RESULT, signal=9)),
                     ('result', dict(EXPECTED_RESULT, stdout='wrong\n')),
                     ('result', dict(EXPECTED_RESULT, signal=False)),
                     ('output', b'name,score\nAda,2\nBo,3\n')]:
    bad = {**good, field: wrong}
    try:
        validate(bad)
    except ValueError:
        continue
    raise RuntimeError('validator accepted invalid ' + field)

run = subprocess.run(['python3', 'capture.py', '--', 'python3', 'normalize.py', 'input.csv', 'output.csv'], capture_output=True)
validate({'wrapper_exit': run.returncode, 'wrapper_stdout': run.stdout,
          'result': json.loads(Path('result.json').read_text()), 'output': Path('output.csv').read_bytes()})
print('PASS gate')
PY
```

The nullable `signal` field accepts only `None` or an integer; booleans are rejected despite Python's integer equality. The wrapper's exit and `CAPTURED` line remain independent from `child_exit`, `timed_out`, `signal`, child stdout, and exact `output.csv` bytes. A faulty wrapper, child failure, timeout, signal, stdout, or artifact must fail before the final `PASS gate`; never replace any child or artifact check with wrapper success.
