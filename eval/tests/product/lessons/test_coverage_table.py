"""Extraction test for the corrected coverage-table recipe.

`references/guides/retro.md`'s Fixture recipe section carries the single-line shell/awk command
that computes the `| Metric | Scope | Measured | Eligible | Result |` table directly from a v2
lifecycle table (plus its optional telemetry sidecar) — replacing the old awk one-liner that
(before this task) read the already-computed coverage table's own columns back, unread, whenever
one happened to be present in the same file. This suite extracts that exact command (never
reimplementing the parsing, the join, or the rounding independently) and runs it over a new,
purpose-built synthetic fixture and its hand-derived golden, plus a mutated copy.

Standard library only; no network, container or model call.
"""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
import sys
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)

HERE = (Path(__file__).resolve().parents[4] / 'eval/lessons')
RETRO = INSTALL / 'references/guides/retro.md'
RETRO_TMPL = INSTALL / 'references/retro.tmpl.md'


def extract_fixture_recipe_command(text=None):
    text = text if text is not None else RETRO.read_text(encoding='utf-8')
    match = re.search(r'Run `(.*?)` from a fixture workspace', text)
    if not match:
        raise AssertionError('no "Run `<command>` from a fixture workspace" sentence found')
    command = match.group(1)
    assert 'eval/' not in command, 'the recipe cites a repository path: ' + command
    return command


def extract_template_row_command(metric, text=None):
    text = text if text is not None else RETRO_TMPL.read_text(encoding='utf-8')
    return text.split('| ' + metric + ' | `', 1)[1].split('`', 1)[0]


def run_in_workspace(command, lifecycle_path, sidecar_path=None):
    with tempfile.TemporaryDirectory(prefix='tackle-learning-loop-') as scratch:
        root = Path(scratch)
        shutil.copyfile(lifecycle_path, root / 'resource-usage.md')
        if sidecar_path is not None:
            shutil.copyfile(sidecar_path, root / 'resource-usage.telemetry.jsonl')
        child = subprocess.run(['sh', '-c', command], cwd=root, capture_output=True, text=True, timeout=30)
    return child


class CoverageTableGoldenTests(unittest.TestCase):
    """C9: the corrected recipe's Measured/Eligible/Result match a hand-derived golden over a new,
    purpose-built fixture (never the four existing coverage-*.md illustrations, which stay
    byte-identical elsewhere), and a mutated input row changes the output."""

    def setUp(self):
        self.lifecycle = HERE / 'fixtures/coverage-lifecycle.md'
        self.sidecar = HERE / 'fixtures/coverage-sidecar.jsonl'
        self.command = extract_fixture_recipe_command()

    def test_golden_tokens_and_duration_with_the_sidecar_present(self):
        child = run_in_workspace(self.command, self.lifecycle, self.sidecar)
        self.assertEqual((child.returncode, child.stderr), (0, ''))
        self.assertEqual(child.stdout.splitlines(), ['tokens 3/5 (60%)', 'duration 2/5 (40%)'])

    def test_no_sidecar_present_yields_zero_measured_tokens_never_a_crash(self):
        child = run_in_workspace(self.command, self.lifecycle, sidecar_path=None)
        self.assertEqual((child.returncode, child.stderr), (0, ''))
        lines = child.stdout.splitlines()
        self.assertEqual(lines[0], 'tokens 0/N (0%)')
        self.assertEqual(lines[1], 'duration 2/5 (40%)', 'duration coverage never depends on the sidecar')

    def test_a_mutated_outcome_changes_the_duration_output(self):
        """The mutated copy: Worker/05's Outcome changed from failed to success, so it now also
        qualifies as a measured (clean, successful, timed) completion."""
        with tempfile.TemporaryDirectory(prefix='tackle-learning-loop-mutant-') as scratch:
            mutated = Path(scratch) / 'mutated-lifecycle.md'
            text = self.lifecycle.read_text(encoding='utf-8')
            marker = '2026-09-20T10:25:00Z | failed | 1 | 0 | blocked'
            self.assertIn(marker, text, 'fixture shape changed; update this mutation to match')
            mutated.write_text(text.replace(marker, '2026-09-20T10:25:00Z | success | 1 | 0 | blocked'), encoding='utf-8')
            child = run_in_workspace(self.command, mutated, self.sidecar)
        self.assertEqual((child.returncode, child.stderr), (0, ''))
        lines = child.stdout.splitlines()
        self.assertEqual(lines[0], 'tokens 3/5 (60%)', 'the mutation only touches Outcome, not the sidecar join')
        self.assertNotEqual(lines[1], 'duration 2/5 (40%)')
        self.assertEqual(lines[1], 'duration 3/5 (60%)')

    def test_empty_lifecycle_table_is_0_over_n_never_a_zero_over_zero_denominator(self):
        with tempfile.TemporaryDirectory(prefix='tackle-learning-loop-empty-') as scratch:
            empty = Path(scratch) / 'empty-lifecycle.md'
            empty.write_text(
                '| Run ID | Event | Task | Role | Harness | Tier | Model | Effort | At | Outcome | '
                'Attempts | Rework | Verification | Source |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n',
                encoding='utf-8')
            child = run_in_workspace(self.command, empty)
        self.assertEqual((child.returncode, child.stderr), (0, ''))
        self.assertEqual(child.stdout.splitlines(), ['tokens 0/N (0%)', 'duration 0/N (0%)'])

    def test_the_legacy_point_column_synonym_does_not_move_any_column(self):
        """The v2 schema's third column is Task; a legacy ledger names it Point instead, at the
        same position, and the recipe must read it identically either way."""
        text = self.lifecycle.read_text(encoding='utf-8')
        self.assertIn('| Run ID | Event | Task | Role |', text)
        renamed = text.replace('| Run ID | Event | Task | Role |', '| Run ID | Event | Point | Role |')
        with tempfile.TemporaryDirectory(prefix='tackle-learning-loop-point-') as scratch:
            renamed_path = Path(scratch) / 'point-lifecycle.md'
            renamed_path.write_text(renamed, encoding='utf-8')
            child = run_in_workspace(self.command, renamed_path, self.sidecar)
        self.assertEqual((child.returncode, child.stderr), (0, ''))
        self.assertEqual(child.stdout.splitlines(), ['tokens 3/5 (60%)', 'duration 2/5 (40%)'])


class SharedRecipeTests(unittest.TestCase):
    """C7: retro.tmpl.md's Lifecycle coverage row embeds the exact same corrected recipe retro.md
    ships, not merely a paraphrase of it; the Exact-token coverage row independently prints
    only the tokens line."""

    def test_retro_md_and_the_lifecycle_coverage_row_share_the_same_awk_program(self):
        guide_command = extract_fixture_recipe_command()
        template_command = extract_template_row_command('**Lifecycle coverage**')
        guide_awk = guide_command.split("awk '", 1)[1].rsplit("'", 1)[0]
        template_awk = template_command.split("awk '", 1)[1].rsplit("'", 1)[0]
        self.assertEqual(guide_awk, template_awk)

    def test_exact_token_coverage_row_prints_only_the_tokens_line(self):
        command = extract_template_row_command('**Exact-token coverage**')
        child = run_in_workspace(command, HERE / 'fixtures/coverage-lifecycle.md', HERE / 'fixtures/coverage-sidecar.jsonl')
        self.assertEqual((child.returncode, child.stderr), (0, ''))
        self.assertEqual(child.stdout.splitlines(), ['tokens 3/5 (60%)'])


if __name__ == '__main__':
    unittest.main()
