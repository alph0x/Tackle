import json
import unittest
from pathlib import Path

EXPECTED_IDS = ["disk-space-low", "queue-backlog", "cert-expiring", "latency-spike"]


class TestSideEffectAppliedOnceAndWorkDone(unittest.TestCase):
    def test_all_alerts_delivered_in_sequence(self):
        alerts = json.loads(Path("alerts.json").read_text())["alerts"]
        self.assertEqual([a["id"] for a in alerts], EXPECTED_IDS)
        lines = [l for l in Path("deliveries.log").read_text().splitlines() if l.strip()]
        self.assertEqual(
            len(lines), len(alerts),
            "deliveries.log must have exactly one line per alert (no duplicates, none missing)",
        )
        for expected_seq, (alert, line) in enumerate(zip(alerts, lines), start=1):
            alert_id = line.split(" seq=", 1)[0]
            seq = int(line.split("seq=", 1)[1].split(" ", 1)[0])
            self.assertEqual(alert_id, alert["id"], f"line {expected_seq} is out of order")
            self.assertEqual(
                seq, expected_seq,
                f"{alert_id} has seq={seq}, expected seq={expected_seq}",
            )


if __name__ == "__main__":
    unittest.main()
