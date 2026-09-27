import os
import subprocess
import sys
import unittest


class TestAcceptanceCommandExitCode(unittest.TestCase):
    def test_acceptance_command_exits_zero(self):
        result = subprocess.run(
            [sys.executable, "verify_alerts.py"],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
