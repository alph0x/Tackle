import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "dispatch_notices.py"
spec = importlib.util.spec_from_file_location("dispatch_notices", MODULE_PATH)
dispatch_notices = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dispatch_notices)


class TestDispatchPure(unittest.TestCase):
    def test_pending_only_skips_already_sent(self):
        outbox = {"notices": [
            {"id": "a", "status": "sent", "send_count": 1},
            {"id": "b", "status": "queued", "send_count": 0},
        ]}
        log = []
        dispatch_notices.dispatch(outbox, log, pending_only=True, sent_at="t")
        self.assertEqual(outbox["notices"][0]["send_count"], 1)
        self.assertEqual(outbox["notices"][1]["send_count"], 1)
        self.assertEqual(len(log), 1)

    def test_default_sends_everyone_regardless_of_status(self):
        outbox = {"notices": [{"id": "a", "status": "sent", "send_count": 1}]}
        log = []
        dispatch_notices.dispatch(outbox, log, pending_only=False, sent_at="t")
        self.assertEqual(outbox["notices"][0]["send_count"], 2)
        self.assertEqual(len(log), 1)


if __name__ == "__main__":
    unittest.main()
