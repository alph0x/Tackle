"""Execute the named workflow block against isolated synthetic repositories."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / 'maintaining/ci_mechanical.py'

class MechanicalChecks(unittest.TestCase):
    def run_fixture(self, workflow, files=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ci = root / '.github/workflows/ci.yml'
            ci.parent.mkdir(parents=True)
            ci.write_text(workflow)
            for name, content in (files or {}).items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            return subprocess.run(['python3', '-I', '-B', str(SCRIPT), '--repo', str(root)], capture_output=True, text=True)

    def test_named_block_runs_and_names_first_failure(self):
        workflow = 'steps:\n  - name: Run the documented mechanical release checks\n    run: |\n      set -eu\n      grep -q wanted eval/README.md\n      exit 7\n  - name: Other\n    run: exit 9\n'
        failure = self.run_fixture(workflow, {'eval/README.md': 'missing'})
        self.assertNotEqual(failure.returncode, 0)
        self.assertIn('eval/README.md', failure.stdout + failure.stderr)
        success = self.run_fixture(workflow.replace('      exit 7\n', ''), {'eval/README.md': 'wanted'})
        self.assertEqual(success.returncode, 0, success.stderr)

        prefix = 'steps:\n  - name: Run the documented mechanical release checks\n    run: |\n'
        cases = [
            ('continued command', 'printf "%s\\n" \\\n  expected\n', 0),
            ('successful exit', 'exit 0\n', 0),
            ('failing exit', 'printf "before\\n"\nexit 7\n', 7),
            ('shell state', 'value=retained\nprintf "%s\\n" "$value"\n', 0),
            ('stderr', 'printf "message\\n" >&2\n', 0),
        ]
        for name, body, status in cases:
            with self.subTest(name=name):
                direct = subprocess.run(['sh', '-c', 'set -eu\n' + body],
                                        capture_output=True, text=True)
                synthetic = prefix + ''.join('      ' + line + '\n' for line in body.splitlines())
                result = self.run_fixture(synthetic)
                self.assertEqual(direct.returncode, status)
                self.assertEqual(result.returncode, status)
                self.assertEqual(result.stdout, direct.stdout)
                if status:
                    self.assertEqual(result.stderr, direct.stderr +
                                     'ci_mechanical: failed (exit 7) at: exit 7\n')
                else:
                    self.assertEqual(result.stderr, direct.stderr)

    def test_direct_run_ignores_nested_keys_and_sibling_steps(self):
        for style in ('|', '|-', '|+'):
            with self.subTest(style=style):
                workflow = (
                    'steps:\n'
                    '  - name: Run the documented mechanical release checks\n'
                    '    env:\n'
                    '      run: |\n'
                    '        exit 91\n'
                    '\n'
                    '    # The command belongs to the step, not its environment.\n'
                    '    run: ' + style + '\n'
                    '      printf "actual\\n"\n'
                    '  - name: Other\n'
                    '    run: |\n'
                    '      exit 92\n'
                )
                result = self.run_fixture(workflow)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, 'actual\n')
                self.assertEqual(result.stderr, '')

    def test_outdented_comment_and_step_name_in_script_content(self):
        workflow = (
            'steps:\n'
            '  - name: Other\n'
            '    run: |\n'
            '      printf "%s\\n" "inert text\n'
            '      - name: Run the documented mechanical release checks\n'
            '      more inert text"\n'
            '  - name: Run the documented mechanical release checks\n'
            '# A workflow comment may appear between the step and its command.\n'
            '    run: |\n'
            '      # Keep shell comments in the command.\n'
            '      printf "actual\\n"\n'
        )
        result = self.run_fixture(workflow)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'actual\n')
        self.assertEqual(result.stderr, '')
        missing = workflow.replace(
            '  - name: Run the documented mechanical release checks\n'
            '# A workflow comment may appear between the step and its command.\n'
            '    run: |\n'
            '      # Keep shell comments in the command.\n'
            '      printf "actual\\n"\n', '')
        result = self.run_fixture(missing)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('expected exactly one mechanical workflow step', result.stderr)

    def test_nested_run_does_not_supply_missing_direct_run(self):
        workflow = (
            'steps:\n'
            '  - name: Run the documented mechanical release checks\n'
            '    env:\n'
            '      run: |\n'
            '        exit 0\n'
            '  - name: Other\n'
            '    run: |\n'
            '      exit 0\n'
        )
        result = self.run_fixture(workflow)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('mechanical workflow step has no literal run block', result.stderr)

    def test_missing_step_fails(self):
        self.assertNotEqual(self.run_fixture('steps:\n  - name: Other\n    run: echo ok\n').returncode, 0)

    def test_nested_trace_is_filtered_and_failure_named(self):
        prefix = 'steps:\n  - name: Run the documented mechanical release checks\n    run: |\n'
        for body, status in [('value=$(printf ok)\nprintf "%s\\n" "$value"\n', 0),
                             ('value=$(printf ok)\nfalse\n', 1)]:
            with self.subTest(status=status):
                workflow = prefix + ''.join('      ' + line + '\n' for line in body.splitlines())
                result = self.run_fixture(workflow)
                self.assertEqual(result.returncode, status)
                self.assertNotIn('__ci_mechanical_trace__', result.stdout + result.stderr)
                if status:
                    self.assertIn('at: false', result.stderr)

    def test_negative_matches_and_install_count_fail_closed(self):
        lines = (ROOT / '.github/workflows/ci.yml').read_text().splitlines()
        gates = {
            'update': next(line.strip() for line in lines if line.strip().startswith('for f in skills/tackle/SKILL.md ')),
            'urls': next(line.strip() for line in lines if line.strip().startswith('[ -d eval/scenarios ]')),
            'wrappers': next(line.strip() for line in lines if line.strip().startswith('python3 -I -B maintaining/ci_mechanical.py --tracked-check wrappers')),
            'count': next(line.strip() for line in lines if line.strip().startswith('[ -d skills/tackle ]')),
        }
        update_files = [
            'skills/tackle/SKILL.md',
            'skills/tackle/references/guides/intake-and-gate.md',
            'skills/tackle/references/guides/update.md',
            'eval/scenarios/s16-self-update-trap/skill/SKILL.md',
            'eval/scenarios/s16-self-update-trap/skill/references/guides/update.md',
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'repo'
            root.mkdir()
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            for name in update_files:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('ordinary content\n')
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
            ci = root / '.github/workflows/ci.yml'
            ci.parent.mkdir(parents=True)
            helper = root / 'maintaining/ci_mechanical.py'
            helper.parent.mkdir(parents=True)
            shutil.copyfile(SCRIPT, helper)

            def run_gate(name, env=None):
                ci.write_text('steps:\n  - name: Run the documented mechanical release checks\n    run: |\n      set -eu\n      ' + gates[name] + '\n')
                return subprocess.run([sys.executable, '-I', '-B', str(SCRIPT), '--repo', str(root)], capture_output=True, text=True, env=env)

            self.assertEqual(run_gate('update').returncode, 0)
            missing = root / update_files[-1]
            missing.unlink()
            failure = run_gate('update')
            self.assertNotEqual(failure.returncode, 0)
            self.assertIn(missing.name, failure.stderr)
            missing.write_text('ordinary content\n')
            (root / update_files[0]).write_text('Download the tag tarball\n')
            self.assertNotEqual(run_gate('update').returncode, 0)
            (root / update_files[0]).write_text('ordinary content\n')

            self.assertEqual(run_gate('urls').returncode, 0)
            scenario = root / update_files[-1]
            scenario.write_text('https://github.com/tackle-fan/Tackle\n')
            self.assertNotEqual(run_gate('urls').returncode, 0)
            scenario.write_text('ordinary content\n')

            success = run_gate('wrappers')
            self.assertEqual(success.returncode, 0)
            self.assertEqual((success.stdout, success.stderr), ('', ''))
            wrapper = root / 'tackle-check'
            wrapper.write_text('')
            subprocess.run(['git', '-C', str(root), 'add', str(wrapper)], check=True)
            failure = run_gate('wrappers')
            self.assertNotEqual(failure.returncode, 0)
            self.assertIn('tackle-check', failure.stderr)
            wrapper.unlink()
            success = run_gate('wrappers')
            self.assertEqual(success.returncode, 0)
            self.assertEqual((success.stdout, success.stderr), ('', ''))

            failure = run_gate('count')
            self.assertNotEqual(failure.returncode, 0)
            self.assertIn('found 3', failure.stderr)
            for i in range(83):
                path = root / 'skills/tackle/scripts' / f'file-{i}'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('')
            subprocess.run(['git', '-C', str(root), 'add', 'skills/tackle'], check=True)
            success = run_gate('count')
            self.assertEqual(success.returncode, 0)
            self.assertEqual((success.stdout, success.stderr), ('', ''))
            extra = root / 'skills/tackle/scripts/extra'
            extra.write_text('')
            subprocess.run(['git', '-C', str(root), 'add', str(extra)], check=True)
            failure = run_gate('count')
            self.assertNotEqual(failure.returncode, 0)
            self.assertIn('found 87', failure.stderr)

            empty_path = Path(temp) / 'bin'
            empty_path.mkdir()
            (empty_path / 'sh').symlink_to('/bin/sh')
            (empty_path / 'python3').symlink_to(sys.executable)
            env = dict(os.environ, PATH=str(empty_path))
            for name, tool in (('update', 'grep'), ('urls', 'git'), ('wrappers', 'git'), ('count', 'git')):
                with self.subTest(missing_tool=name):
                    failure = run_gate(name, env)
                    self.assertNotEqual(failure.returncode, 0)
                    self.assertIn(tool, failure.stderr)
                    self.assertIn('not found', failure.stderr)

    def test_relative_repo_matches_absolute(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'repo'
            ci = root / '.github/workflows/ci.yml'
            ci.parent.mkdir(parents=True)
            ci.write_text('steps:\n  - name: Run the documented mechanical release checks\n    run: |\n      exit 7\n')
            command = ['python3', '-I', '-B', str(SCRIPT), '--repo']
            absolute = subprocess.run(command + [str(root)], cwd=temp, capture_output=True)
            relative = subprocess.run(command + ['repo'], cwd=temp, capture_output=True)
            self.assertEqual((absolute.returncode, absolute.stderr), (relative.returncode, relative.stderr))
