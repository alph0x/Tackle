"""The protected retro clock oracle follows its named section, run as the real protected method on edited copies."""
from pathlib import Path
import importlib.util
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('protected_history_templates', HERE / 'test_history_and_obligation_templates.py')
protected = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protected)
METHOD = 'test_r04_the_clock_format_and_its_unmeasured_clocks_are_stated_in_each_home'
SECTION = '### Fixture recipe\n'


class ClockOracleSectionTests(unittest.TestCase):
    def run_protected(self, edit):
        """Run the protected method on a copy of the references whose retro guide passed through edit."""
        with tempfile.TemporaryDirectory(prefix='tackle-clock-oracle-') as temporary:
            ref = Path(temporary) / 'references'
            shutil.copytree(protected.REF, ref)
            guide = ref / 'guides/retro.md'
            guide.write_text(edit(guide.read_text(encoding='utf-8')), encoding='utf-8')
            saved = (protected.REF, protected.GUIDES)
            protected.REF, protected.GUIDES = ref, ref / 'guides'
            try:
                result = unittest.TestResult()
                protected.RetroRecipeTests(METHOD).run(result)
            finally:
                protected.REF, protected.GUIDES = saved
            return result

    def assert_oracle_passes(self, edit):
        result = self.run_protected(edit)
        self.assertEqual((result.testsRun, result.failures, result.errors), (1, [], []))

    def assert_oracle_fails(self, edit, message=None):
        result = self.run_protected(edit)
        self.assertEqual((result.testsRun, len(result.failures), result.errors), (1, 1, []))
        if message is not None:
            self.assertIn(message, result.failures[0][1])

    def test_unchanged_guide_satisfies_the_oracle(self):
        self.assert_oracle_passes(lambda guide: guide)

    def test_earlier_unrelated_paragraphs_keep_the_oracle_valid(self):
        paragraphs = 'An unrelated paragraph.\n\nAnother unrelated paragraph spanning\ntwo lines.\n\n'
        self.assert_oracle_passes(lambda guide: guide.replace('## Metrics', paragraphs + '## Metrics', 1))

    def test_removed_or_changed_clock_guidance_fails_the_oracle(self):
        clock = 'YYYY-MM-DDTHH:MM:SS[.fff](Z|±HH:MM)'
        for old, new in ((clock, 'YYYY-MM-DD HH:MM'), ('minute-only', 'coarse'), ('space-separated', 'blank-joined'),
                         ('unmeasured', 'ignored')):
            section = lambda guide: guide.split(SECTION, 1)[1].split('\n## ', 1)[0]
            edit = lambda guide, old=old, new=new: guide.split(SECTION, 1)[0] + SECTION + section(guide).replace(old, new) + \
                guide.split(SECTION, 1)[1][len(section(guide)):]
            self.assert_oracle_fails(edit)

    def test_clock_guidance_outside_the_section_cannot_satisfy_the_oracle(self):
        self.assert_oracle_fails(lambda guide: guide.replace(SECTION, '### Worked example\n', 1))
        self.assert_oracle_fails(lambda guide: guide.replace(SECTION, SECTION + '\n### Worked example\n', 1))

    def test_missing_section_is_reported_by_name(self):
        self.assert_oracle_fails(lambda guide: guide.replace(SECTION, '', 1), 'missing retro fixture recipe section')


if __name__ == '__main__':
    unittest.main()
