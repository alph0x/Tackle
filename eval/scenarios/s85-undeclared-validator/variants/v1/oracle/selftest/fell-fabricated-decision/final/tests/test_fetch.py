import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from sync.fetch import fetch_feed


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.body


class FetchTests(unittest.TestCase):
    def test_returns_text(self):
        self.assertEqual(fetch_feed("u", lambda url: FakeResponse(b"a,b")), "a,b")


if __name__ == "__main__":
    unittest.main()
