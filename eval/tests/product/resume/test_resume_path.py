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
# their sources and scopes from the sentence: a source it does not name is not read, and a receipt scope
# of "current" reads only the newest report.
NEGATION = re.compile(r"\b(never|nor|nothing)\b", re.I)


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
    """`reports` runs oldest first; the last one is the current task's."""
    low = sentence.lower()
    found = set()
    if "table" in low:
        found |= table_open(board)
    if "remains" in low or "receipt" in low:
        found |= receipt_ids(reports[-1:] if "current" in low else reports)
    return found


BOARD = ("| Obligation | What | Owner | Trigger | State | Discharge check | Reference |\n"
         "|---|---|---|---|---|---|---|\n| O-01 | a | owner | t | Open | c | - |\n"
         "| O-03 | b | owner | t | Discharged | c | a/ref.md |\n")
# An older Complete report holds the only copy of O-02; the current task's receipt is none.
REPORTS = ["Final status: Complete.\n**Remains**: O-02\n", "Final status: Complete.\n**Remains**: none\n"]


def listing_problems(sentence, board=BOARD, reports=REPORTS):
    """What is wrong with a sentence that must list every Open obligation and every receipt id."""
    problems = []
    if NEGATION.search(sentence):
        problems.append("negated")
    if list_open_obligations(sentence, board, reports) != {"O-01", "O-02"}:
        problems.append("misses an obligation held only in an older Complete report")
    if "every" not in sentence.lower():
        problems.append("not every")
    return problems


def closure_problems(sentence):
    problems = listing_problems(sentence)
    if "before an initiative is declared closed" not in sentence.lower():
        problems.append("not before closure")
    return problems


def spent_problems(sentences_):
    """What is wrong with Correction lineage's account of the spent count."""
    text = " ".join(sentences_).lower()
    problems = []
    for needed in ("task-linked failed correction-validation records", "snapshot only projects",
                   "never assumes zero", "zero requires records showing no failure",
                   "no further attempt", "reconciled"):
        if needed not in text:
            problems.append("missing: " + needed)
    for banned in ("starts from zero", "makes another attempt", "state snapshot; the task-linked"):
        if banned in text:
            problems.append("says: " + banned)
    return problems


def spent_count(sentence, records):
    """Count the task's failed correction validations from `records`; a missing source is not zero."""
    if "record" not in sentence.lower() or records is None:
        return None
    return len({r["event"] for r in records if r["task"] == "task-a" and r["failed"]})


def mutate(text, old, new):
    assert old in text, old
    return text.replace(old, new)


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
        listing = pick(" ".join(status), "every", "open", "obligation", "receipt")
        self.assertTrue(has(sentence, "cold resume") or listing, "cold-resume half missing")
        self.assertEqual(closure_problems(sentence), [])
        self.assertEqual(listing_problems(listing), [])
        self.assertEqual(list_open_obligations(sentence, "", REPORTS), {"O-02"}, "no table: receipts alone")
        self.assertNotEqual(table_open(BOARD), {"O-01", "O-02"}, "a table-only reader misses the receipt id")
        # Each mutant is a wrong text the shipped checks must refuse.
        closure_mutants = {
            "negated listing": mutate(sentence, "list every", "never list every"),
            "current task's receipt only": mutate(sentence, "a Complete task's", "the current task's"),
            "after closure": mutate(sentence, "Before an initiative", "After an initiative"),
        }
        for name, mutant in closure_mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(closure_problems(mutant), [])
        listing_mutants = {
            "negated listing": mutate(listing, "lists every", "never lists every"),
            "current receipt only": mutate(listing, "from every", "from the current"),
        }
        for name, mutant in listing_mutants.items():
            with self.subTest(mutant=name):
                self.assertNotEqual(listing_problems(mutant), [])

    def test_spent_count_source_is_named_and_never_zero(self):
        lineage = section(read("guides/run.md"), "Correction lineage")
        sentence = pick(lineage, "spent", "count", "record")
        self.assertTrue(has(sentence, "failed"), sentence)
        self.assertEqual(spent_problems(sentences(lineage)), [])
        records = [{"task": "task-a", "event": "E-1", "failed": True, "actor": "executor"},
                   {"task": "task-a", "event": "E-2", "failed": True, "actor": "coordinator"},
                   {"task": "task-a", "event": "E-2", "failed": True, "actor": "coordinator"},
                   {"task": "task-b", "event": "E-3", "failed": True, "actor": "executor"}]
        self.assertEqual(spent_count(sentence, records), 2)
        self.assertEqual(spent_count(sentence, records[3:]), 0, "records showing no failure for the task are zero")
        self.assertIsNone(spent_count(sentence, None), "missing records never read as zero")
        text = " ".join(sentences(lineage))
        for name, old, new in (
                ("starts from zero", "A resume never assumes zero", "A resume starts from zero"),
                ("another attempt", "makes no further attempt", "makes another attempt"),
                ("snapshot is the source", "the State snapshot only projects it",
                 "the State snapshot is the source; the records only project it")):
            with self.subTest(mutant=name):
                self.assertNotEqual(spent_problems(sentences(mutate(text, old, new))), [])
        self.assertNotEqual(spent_problems(sentences(mutate(text, "never assumes zero; zero requires records showing no failure", "never starts from zero")))
                            , [], "a literal ban on zero forbids a task with no failures")


if __name__ == "__main__":
    unittest.main()
