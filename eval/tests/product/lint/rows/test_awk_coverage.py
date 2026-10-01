"""Report AWK variants only after the canonical row consumer invokes them."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import test_lint_rows as base

REQUIRED = ('gawk', 'mawk', 'original-awk', 'busybox')
MARKER = 'TACKLE_AWK_COVERAGE='


class AwkCoverageTests(unittest.TestCase):
    def test_reports_actual_host_invocations_and_missing_variants(self):
        with tempfile.TemporaryDirectory(prefix='tackle-awk-coverage-') as temporary:
            root_dir = Path(temporary)
            fixture_root = Path(os.environ['TACKLE_AWK_FIXTURE_BIN']).resolve() if os.environ.get('TACKLE_AWK_FIXTURE_BIN') else None
            path_parts = [part for part in os.environ.get('PATH', '').split(os.pathsep) if part]
            host_path_parts = [part for part in path_parts
                               if fixture_root is None or not Path(part).resolve().is_relative_to(fixture_root)]
            host_path = os.pathsep.join(host_path_parts)

            def workspace(name):
                root = root_dir / name / 'root'
                root.mkdir(parents=True)
                base.materialize(root, 'pass-full')
                return root

            def invoke(label, command, path, log):
                old_path = os.environ.get('PATH')
                old_log = os.environ.get('TACKLE_AWK_INVOCATIONS')
                os.environ['PATH'] = path
                os.environ['TACKLE_AWK_INVOCATIONS'] = str(log)
                try:
                    verdict, child = base.run_row(12, workspace(label), command)
                finally:
                    if old_path is None:
                        os.environ.pop('PATH', None)
                    else:
                        os.environ['PATH'] = old_path
                    if old_log is None:
                        os.environ.pop('TACKLE_AWK_INVOCATIONS', None)
                    else:
                        os.environ['TACKLE_AWK_INVOCATIONS'] = old_log
                self.assertEqual(verdict, 'PASS', (child.returncode, child.stdout[:400], child.stderr[:400]))
                self.assertEqual(child.returncode, 0)

            old_path = os.environ.get('PATH')
            os.environ['PATH'] = host_path
            try:
                host_variants = base.awk_variants()
                host_log = root_dir / 'host-invocations.log'
                host_log.write_text('')
                for name, command in host_variants:
                    with self.subTest(host_variant=name):
                        invoke('host-' + name, command, host_path, host_log)
            finally:
                if old_path is None:
                    os.environ.pop('PATH', None)
                else:
                    os.environ['PATH'] = old_path

            invoked = set(host_log.read_text().splitlines())
            self.assertIn('system', invoked)
            for name, command in host_variants:
                self.assertIn(name, invoked, (name, command, host_log.read_text()))
            host_executed = [name for name in REQUIRED if name in invoked]
            host_missing = [name for name in REQUIRED if name not in invoked]

            fake_bin = root_dir / 'fake-gawk-bin'
            fake_bin.mkdir()
            fake_gawk = fake_bin / 'gawk'
            fake_gawk.write_text('#!/bin/sh\nprintf "%s\\n" "sentinel:gawk" >> "$TACKLE_AWK_INVOCATIONS"\nexec /usr/bin/awk "$@"\n')
            fake_gawk.chmod(0o755)
            fake_log = root_dir / 'fake-gawk-invocations.log'
            fake_log.write_text('')
            invoke('fake-gawk', [str(fake_gawk)], str(fake_bin) + os.pathsep + host_path, fake_log)
            fake_events = fake_log.read_text().splitlines()
            self.assertIn('gawk', fake_events)
            self.assertIn('sentinel:gawk', fake_events)
            self.assertLess(fake_events.index('gawk'), fake_events.index('sentinel:gawk'))
            fake_executed = ['gawk'] if 'gawk' in fake_events else []

            unused_bin = root_dir / 'unused-mawk-bin'
            unused_bin.mkdir()
            unused_mawk = unused_bin / 'mawk'
            unused_sentinel = root_dir / 'unused-mawk-sentinel'
            unused_mawk.write_text('#!/bin/sh\nprintf "%s\\n" "mawk" >> "$TACKLE_AWK_INVOCATIONS"\n: > "$TACKLE_AWK_UNUSED_SENTINEL"\nexec /usr/bin/awk "$@"\n')
            unused_mawk.chmod(0o755)
            unused_path = str(unused_bin) + os.pathsep + host_path
            old_path = os.environ.get('PATH')
            old_unused_sentinel = os.environ.get('TACKLE_AWK_UNUSED_SENTINEL')
            os.environ['PATH'] = unused_path
            os.environ['TACKLE_AWK_UNUSED_SENTINEL'] = str(unused_sentinel)
            try:
                discovered = {name for name, command in base.awk_variants()}
                self.assertIn('mawk', discovered)
                unused_log = root_dir / 'unused-mawk-invocations.log'
                unused_log.write_text('')
                invoke('system-with-unused-mawk', None, unused_path, unused_log)
            finally:
                if old_path is None:
                    os.environ.pop('PATH', None)
                else:
                    os.environ['PATH'] = old_path
                if old_unused_sentinel is None:
                    os.environ.pop('TACKLE_AWK_UNUSED_SENTINEL', None)
                else:
                    os.environ['TACKLE_AWK_UNUSED_SENTINEL'] = old_unused_sentinel
            unused_events = unused_log.read_text().splitlines()
            self.assertNotIn('mawk', unused_events)
            self.assertFalse(unused_sentinel.exists())

            busybox_bin = root_dir / 'busybox-no-applet-bin'
            busybox_bin.mkdir()
            busybox = busybox_bin / 'busybox'
            busybox.write_text('#!/bin/sh\nif [ "$1" = awk ]; then exit 23; fi\nexit 64\n')
            busybox.chmod(0o755)
            busybox_path = str(busybox_bin) + os.pathsep + host_path
            old_path = os.environ.get('PATH')
            os.environ['PATH'] = busybox_path
            try:
                busybox_discovered = {name for name, command in base.awk_variants()}
            finally:
                if old_path is None:
                    os.environ.pop('PATH', None)
                else:
                    os.environ['PATH'] = old_path
            self.assertNotIn('busybox', busybox_discovered)

            ci_good_bin = root_dir / 'ci-good-bin'
            ci_good_bin.mkdir()
            for name in ('gawk', 'mawk', 'original-awk'):
                executable = ci_good_bin / name
                executable.write_text('#!/bin/sh\nexec /usr/bin/awk "$@"\n')
                executable.chmod(0o755)
            ci_good_busybox = ci_good_bin / 'busybox'
            ci_good_busybox.write_text('#!/bin/sh\n[ "$1" = awk ] || exit 64\nshift\nexec /usr/bin/awk "$@"\n')
            ci_good_busybox.chmod(0o755)
            ci_probe = root_dir / 'ci-awk-prerequisite.sh'
            ci_probe.write_text('set -eu\nfor a in gawk mawk original-awk busybox; do command -v "$a" >/dev/null || { echo "missing awk: $a"; exit 1; }; done\nbusybox awk \'BEGIN { exit 0 }\' || { echo "busybox has no awk applet"; exit 1; }\n')
            ci_good_env = os.environ.copy()
            ci_good_env['PATH'] = str(ci_good_bin) + os.pathsep + host_path
            ci_good_result = subprocess.run(['sh', str(ci_probe)], cwd=root_dir, env=ci_good_env, capture_output=True, text=True)
            self.assertEqual(ci_good_result.returncode, 0, (ci_good_result.returncode, ci_good_result.stdout, ci_good_result.stderr))

            ci_bin = root_dir / 'ci-no-applet-bin'
            ci_bin.mkdir()
            for name in ('gawk', 'mawk', 'original-awk'):
                executable = ci_bin / name
                executable.write_text('#!/bin/sh\nexec /usr/bin/awk "$@"\n')
                executable.chmod(0o755)
            ci_busybox = ci_bin / 'busybox'
            ci_busybox.write_text('#!/bin/sh\nif [ "$1" = awk ]; then exit 23; fi\nexit 64\n')
            ci_busybox.chmod(0o755)
            ci_env = os.environ.copy()
            ci_env['PATH'] = str(ci_bin) + os.pathsep + host_path
            ci_result = subprocess.run(['sh', str(ci_probe)], cwd=root_dir, env=ci_env, capture_output=True, text=True)
            self.assertEqual(ci_result.returncode, 1, (ci_result.returncode, ci_result.stdout, ci_result.stderr))
            self.assertIn('busybox has no awk applet', ci_result.stdout + ci_result.stderr)

            report = {
                'system_status': 'executed' if 'system' in invoked else 'missing',
                'host_executed': host_executed,
                'host_missing': host_missing,
                'fixture_probes': {
                    'fake_gawk': {'executed': fake_executed, 'sentinel_after_invocation': True},
                    'found_uninvoked_mawk': {'discovered': True, 'executed': False, 'counted_as_executed': False},
                    'busybox_without_applet': {'discovered': False, 'counted_as_missing': True,
                                               'ci_prerequisite_exit': ci_result.returncode,
                                               'ci_applet_capable_exit': ci_good_result.returncode},
                },
            }
            print(MARKER + json.dumps(report, sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    unittest.main()
