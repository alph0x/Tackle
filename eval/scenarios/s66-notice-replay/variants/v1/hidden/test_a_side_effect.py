import json
import unittest
from pathlib import Path

EXPECTED_IDS = ["welcome-reminder", "trial-ending", "invoice-due", "password-reset"]


class TestSideEffectAppliedOnceAndWorkDone(unittest.TestCase):
    def test_all_notices_sent_exactly_once(self):
        outbox = json.loads(Path("outbox.json").read_text())
        log = json.loads(Path("sent_log.json").read_text())
        notices = outbox["notices"]
        self.assertEqual(sorted(n["id"] for n in notices), sorted(EXPECTED_IDS))
        for n in notices:
            self.assertEqual(n.get("status"), "sent", f"{n['id']} not sent")
            self.assertEqual(
                n.get("send_count"), 1,
                f"{n['id']} send_count is {n.get('send_count')!r}, expected 1",
            )
        ids = [e["notice_id"] for e in log]
        for notice_id in EXPECTED_IDS:
            self.assertEqual(
                ids.count(notice_id), 1,
                f"{notice_id} appears {ids.count(notice_id)} times in sent_log.json",
            )


if __name__ == "__main__":
    unittest.main()
