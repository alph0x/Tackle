"""The resume path: one cold-resume read order, the spent-count source and the closure listing."""
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)
REFS = INSTALL / "references"
ANCHOR = "cold-resume-read-order"


def read(rel):
    return (REFS / rel).read_text(encoding="utf-8")


def section(text, heading):
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if re.fullmatch(r"##\s+%s\s*" % re.escape(heading), line)]
    assert len(starts) == 1, "%d sections headed %r" % (len(starts), heading)
    end = next((j for j in range(starts[0] + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
    return "\n".join(lines[starts[0] + 1:end])


def sentences(text):
    flat = re.sub(r"\s+", " ", re.sub(r"^\s*(?:\d+\.|[-*])\s+", " ", text, flags=re.M))
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+(?=[A-Z`(\[])", flat) if s.strip()]


def has(sentence, *words):
    return all(w.lower() in sentence.lower() for w in words)


def pick(text, *words):
    hits = [s for s in sentences(text) if has(s, *words)]
    assert hits, "no sentence holds %s" % (words,)
    return hits[0]


# The consumers below read a fixture workspace the way the shipped sentence says to read it. They take
# their sources from the sentence: a source it does not name is not read.
def table_open(board):
    found = set()
    for line in board.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if re.fullmatch(r"O-\d\d", cells[0]) and "Open" in cells:
            found.add(cells[0])
    return found


def receipt_ids(reports):
    found = set()
    for body in reports:
        for line in body.split("\n"):
            if line.startswith("**Remains**:"):
                found |= set(re.findall(r"O-\d\d", line))
    return found


def list_open_obligations(sentence, board, reports):
    low = sentence.lower()
    found = set()
    if "obligations table" in low or "table" in low:
        found |= table_open(board)
    if "remains" in low or "receipt" in low:
        found |= receipt_ids(reports)
    return found


def spent_count(sentence, records):
    """Count the task's failed correction validations from `records`; a missing source is not zero."""
    if "record" not in sentence.lower() or records is None:
        return None
    seen = {r["event"] for r in records if r["task"] == "T-9" and r["failed"]}
    return len(seen)


class ResumePathTests(unittest.TestCase):
    def test_cold_resume_order_is_defined_once_and_every_list_links_to_it(self):
        status = read("guides/status.md")
        self.assertEqual(status.count("## Cold resume read order"), 1)
        self.assertIn('<a id="%s"></a>\n## Cold resume read order' % ANCHOR, status)
        body = section(status, "Cold resume read order")
        items = re.findall(r"^\d+\.\s+(.*(?:\n(?!\d+\.|\s*$).*)*)", body, re.M)
        self.assertEqual(len(items), 5)
        for item, words in zip(items, (("AGENTS.md",), ("task-board.md", "sha256", "obligation"),
                                       ("snapshot",), ("brief", "report"), ("input",))):
            self.assertTrue(has(item, *words), item)
        self.assertTrue(any(has(s, "receipt", "complete") for s in sentences(body)))
        self.assertTrue(any(has(s, "board wins") for s in sentences(body)))
        bound = [s for s in sentences(body) if "history-archive.md" in s]
        self.assertEqual(len(bound), 1)
        self.assertIn("only when", bound[0])
        for other in ("board wins", "receipt", "lists every", "list every", "in this order"):
            self.assertNotIn(other, bound[0].lower())
        self.assertIn("](#%s)" % ANCHOR, re.search(r"^- \*\*Resume\*\*.*", status, re.M).group(0))
        link = re.compile(r"\]\([^)\s]*status\.md#%s\)" % ANCHOR)
        card = read("guides/run-card.md")
        self.assertRegex(section(card, "Depth (on demand)"), link)
        self.assertEqual(len(link.findall(card)), 1, "a card link outside Depth enters the RUN chain")
        self.assertRegex(read("guides/intake-and-gate.md"), link)
        named = re.compile(r"`[^`\s]*status\.md#%s`" % ANCHOR)
        self.assertRegex(read("AGENTS.tmpl.md"), named)
        self.assertRegex(section(read("README.tmpl.md"), "Reading order (new agent / human)"), named)

    def test_closure_and_cold_resume_list_every_open_obligation(self):
        run = read("guides/run.md")
        close = section(run, "Integration and deliverable acceptance")
        sentence = pick(close, "every", "open", "obligation", "remains")
        self.assertTrue(has(sentence, "closed") or has(sentence, "closure"), sentence)
        status = sentences(section(read("guides/status.md"), "Cold resume read order"))
        self.assertTrue(has(sentence, "cold resume") or any(
            has(s, "every", "open", "obligation", "receipt") for s in status), "cold-resume half missing")
        board = ("| Obligation | What | Owner | Trigger | State | Discharge check | Reference |\n"
                 "|---|---|---|---|---|---|---|\n| O-01 | a | owner | t | Open | c | - |\n"
                 "| O-03 | b | owner | t | Discharged | c | D-01 |\n")
        reports = ["Final status: Complete.\n**Remains**: O-02\n", "Final status: Complete.\n**Remains**: none\n"]
        listed = list_open_obligations(sentence, board, reports)
        self.assertEqual(listed, {"O-01", "O-02"})
        self.assertNotEqual(table_open(board), listed, "a table-only reader misses the receipt-held obligation")
        self.assertEqual(list_open_obligations(sentence, "", reports), {"O-02"}, "no table: receipts alone")

    def test_spent_count_source_is_named_and_never_zero(self):
        lineage = section(read("guides/run.md"), "Correction lineage")
        sentence = pick(lineage, "spent", "count", "record")
        self.assertTrue(has(sentence, "failed"), sentence)
        self.assertTrue(any(has(s, "never", "zero") for s in sentences(lineage)))
        self.assertTrue(any(has(s, "snapshot", "project") for s in sentences(lineage)))
        records = [{"task": "T-9", "event": "E-1", "failed": True, "actor": "executor"},
                   {"task": "T-9", "event": "E-2", "failed": True, "actor": "coordinator"},
                   {"task": "T-9", "event": "E-2", "failed": True, "actor": "coordinator"},
                   {"task": "T-8", "event": "E-3", "failed": True, "actor": "executor"}]
        self.assertEqual(spent_count(sentence, records), 2)
        self.assertIsNone(spent_count(sentence, None), "missing records never read as zero")
        self.assertTrue(any(has(s, "reconcil") for s in sentences(lineage)))


if __name__ == "__main__":
    unittest.main()
