"""Run one hidden acceptance suite and write its counts as JSON. Invoked only by judge.py, as

    python3 -I runner.py <hidden dir> <copy> <result file> [<pythonpath entry> ...]

Isolated mode (-I) ignores PYTHONPATH, the working directory and any sitecustomize, so nothing in the
judged copy runs before this file. The runner checks that unittest is the standard library's, appends the
copy's pythonpath entries after the standard library, and discovers the suite programmatically. The judge
reads only the result file, never the text output. Exit 0 means the suite was successful.
"""
import json
import os
import sys
import sysconfig


def main(argv):
    hidden, copy, result = argv[:3]
    sys.dont_write_bytecode = True
    import unittest
    stdlib = os.path.realpath(sysconfig.get_paths()['stdlib'])
    if not os.path.realpath(unittest.__file__).startswith(stdlib + os.sep):
        sys.stderr.write('runner: unittest does not come from the standard library\n')
        return 3
    for entry in argv[3:]:
        sys.path.append(os.path.normpath(os.path.join(copy, entry)))
    suite = unittest.TestLoader().discover(hidden, pattern='test_*.py', top_level_dir=hidden)
    outcome = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    counts = {'ran': outcome.testsRun, 'failures': len(outcome.failures), 'errors': len(outcome.errors),
              'skipped': len(outcome.skipped), 'expected_failures': len(outcome.expectedFailures),
              'unexpected_successes': len(outcome.unexpectedSuccesses)}
    with open(result, 'w', encoding='utf-8') as handle:
        json.dump(counts, handle)
    return 0 if outcome.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
