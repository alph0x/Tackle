import tempfile
import unittest
from pathlib import Path

from normalize import write_results


class Normalize(unittest.TestCase):
    def test_writes_both_declared_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            write_results(temp)
            root = Path(temp)
            self.assertEqual(root.joinpath("result.csv").read_bytes(), b"name,score\nBo,3\nAda,2\n")
            self.assertEqual(set(__import__("json").loads(root.joinpath("result.json").read_text())), {"name", "score"})


if __name__ == "__main__":
    unittest.main()
