import copy
from pathlib import Path
import runpy
import unittest


ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / 'skills/tackle/scripts/correction_lineage.py'
LINEAGE = runpy.run_path(str(SOURCE))


def failed_events(pool, count):
    return [dict(cycle_id=f'{pool}-{index}', pool_id=pool,
                 kind='failed-correction') for index in range(1, count + 1)]


class CorrectionRecovery(unittest.TestCase):
    def test_default_stop_can_resume_only_under_explicit_ceiling(self):
        events = failed_events('task', 3)
        default = LINEAGE['correction_usage'](events, ['task'])
        self.assertEqual((default['spent'], default['remaining'], default['exhausted']),
                         (3, 0, True))

        approved = LINEAGE['correction_usage'](
            events, ['task'], approved_limits={'task': 5})
        self.assertEqual((approved['spent'], approved['remaining'], approved['exhausted']),
                         (3, 2, False))
        duplicate = LINEAGE['correction_usage'](
            events + [events[-1]], ['task'], approved_limits={'task': 5})
        self.assertEqual(duplicate['spent'], 3)

        next_failure = events + failed_events('task', 4)[-1:]
        after_one = LINEAGE['correction_usage'](
            next_failure, ['task'], approved_limits={'task': 5})
        self.assertEqual((after_one['spent'], after_one['remaining'], after_one['exhausted']),
                         (4, 1, False))
        next_failure += failed_events('task', 5)[-1:]
        exhausted = LINEAGE['correction_usage'](
            next_failure, ['task'], approved_limits={'task': 5})
        self.assertEqual((exhausted['spent'], exhausted['remaining'], exhausted['exhausted']),
                         (5, 0, True))

    def test_approval_changes_only_named_pool_and_combined_pools_still_stop(self):
        events = failed_events('alpha', 3) + failed_events('beta', 3)
        selected = ['alpha', 'beta']
        approved_limits = {'alpha': 4}
        result = LINEAGE['correction_usage'](
            events, selected, approved_limits=approved_limits)
        self.assertEqual(result['pools'], {'alpha': 3, 'beta': 3})
        self.assertEqual(result['remaining'], 0)
        self.assertTrue(result['exhausted'])

        alpha_only = LINEAGE['correction_usage'](
            events, ['alpha'], approved_limits=approved_limits)
        self.assertEqual((alpha_only['remaining'], alpha_only['exhausted']), (1, False))
        self.assertEqual(selected, ['alpha', 'beta'])
        self.assertEqual(approved_limits, {'alpha': 4})

    def test_invalid_approved_ceiling_and_unapproved_legacy_limit_are_rejected(self):
        for ceiling in (True, 4.0, 0, 2, 3):
            with self.subTest(ceiling=ceiling):
                with self.assertRaisesRegex(ValueError, 'approved pool ceiling'):
                    LINEAGE['correction_usage'](
                        [], ['task'], approved_limits={'task': ceiling})
        with self.assertRaisesRegex(ValueError, 'approved pool ceiling'):
            LINEAGE['correction_usage']([], ['task'], approved_limits={'other': 4})
        with self.assertRaisesRegex(ValueError, 'pool limit'):
            LINEAGE['correction_usage']([], ['task'], limits={'task': 5})

    def test_resume_and_transfer_keep_spent_events_and_input_mappings(self):
        events = failed_events('old-task', 3)
        previous = ['failure-1']
        descendants = {'T-NEW': ['failure-1']}
        unresolved = ['failure-1']
        failure_pools = {'failure-1': 'old-task'}
        inputs = copy.deepcopy((events, previous, descendants, unresolved, failure_pools))

        transferred = LINEAGE['transfer_lineage'](
            previous, descendants, unresolved, failure_pools)
        self.assertEqual(transferred, {'T-NEW': ['old-task']})
        resumed = runpy.run_path(str(SOURCE))
        result = resumed['correction_usage'](
            events, transferred['T-NEW'], approved_limits={'old-task': 5})
        self.assertEqual((result['spent'], result['remaining'], result['exhausted']),
                         (3, 2, False))
        self.assertEqual((events, previous, descendants, unresolved, failure_pools), inputs)

    def test_unowned_pool_keeps_two_default_and_needs_explicit_three(self):
        events = failed_events('integration', 2)
        limits = {'integration': 2}
        default = LINEAGE['correction_usage'](events, ['integration'], limits=limits)
        self.assertEqual((default['spent'], default['remaining'], default['exhausted']),
                         (2, 0, True))
        approved = LINEAGE['correction_usage'](
            events, ['integration'], limits=limits,
            approved_limits={'integration': 3})
        self.assertEqual((approved['spent'], approved['remaining'], approved['exhausted']),
                         (2, 1, False))
        exhausted = LINEAGE['correction_usage'](
            events + failed_events('integration', 3)[-1:], ['integration'],
            limits=limits, approved_limits={'integration': 3})
        self.assertEqual((exhausted['spent'], exhausted['remaining'], exhausted['exhausted']),
                         (3, 0, True))

    def test_conflicting_event_still_fails_under_approved_ceiling(self):
        original = dict(cycle_id='same', pool_id='task', kind='failed-correction')
        conflicting = dict(original, pool_id='other')
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            LINEAGE['correction_usage'](
                [original, conflicting], ['task'], approved_limits={'task': 5})
