"""Every /Users check refuses a spelling the volume folds to /Users, not only ASCII case variants.

APFS folds U+017F LATIN SMALL LETTER LONG S to 's', so '/Uſers' names /Users on the host. The run-root and
launcher checks fold with casefold(); the oracle interpreter check must fold the same way, or that spelling slips
past the explicit refusal and the route only learns of it when the sandbox denies the interpreter after the model
call. Model-free: the configuration is read and judged in process.
"""
import unittest
from pathlib import Path
from types import SimpleNamespace

from test_subscription_route import Base, SEP, route

LONG_S = 'ſ'


class LongSFolding(Base):
    def test_a_long_s_spelling_of_users_is_refused_by_every_check(self):
        env = self.env
        cfg = env.config()
        cfg['oracle']['denied_prefixes'] = []
        env.write_config(cfg)
        loaded = route.load_config(env.config_path)
        for spelling in ('U%sers' % LONG_S, 'U%ser%s' % (LONG_S, LONG_S)):
            variant = SimpleNamespace(**vars(loaded))
            variant.oracle_python = SEP + spelling + '/someone/tools/python3'
            self.assertIn('oracle interpreter is under', route.judge_refusal(variant) or '', spelling)
            variant = SimpleNamespace(**vars(loaded))
            variant.run_root = Path(SEP + spelling + '/someone/rr')
            self.assertIn('run root is under', route.judge_refusal(variant) or '', spelling)
            variant = SimpleNamespace(**vars(loaded))
            variant.launcher = SEP + spelling + '/someone/launcher'
            self.assertIn('launcher is under', route.judge_refusal(variant) or '', spelling)


if __name__ == '__main__':
    unittest.main()
