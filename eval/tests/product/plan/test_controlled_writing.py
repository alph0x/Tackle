"""The controlled-writing script judges fixture texts, and the shipped guide passes its own check."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval" / "plan"))
from maintaining.install_root import current_root  # noqa: E402
import controlled_writing_cases as fixtures  # noqa: E402

INSTALL = current_root(ROOT)
FORBIDDEN = {"socket", "ssl", "urllib", "http", "subprocess", "requests", "asyncio", "webbrowser", "os", "shutil"}


def load_recipe():
    path = INSTALL / "scripts/controlled_writing.py"
    source = path.read_text(encoding="utf-8")
    assert "```" not in source, "the script is a Python file, not a Markdown fence"
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & FORBIDDEN, "the script imports %s" % sorted(imported & FORBIDDEN)
    spec = importlib.util.spec_from_file_location("controlled_writing", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return vars(module)


class ControlledWriting(unittest.TestCase):
    def test_the_shipped_script_judges_fixture_texts(self):
        namespace = load_recipe()
        findings = namespace["findings"]
        self.assertTrue({"en", "es"} <= set(namespace["LANGUAGES"]))
        for name, text, language, expected in fixtures.cases():
            with self.subTest(case=name):
                found = findings(text, language)
                for item in found:
                    self.assertEqual(set(item), {"line", "kind", "detail"})
                got = {(item["kind"], item["line"]) for item in found}
                if not expected:
                    self.assertEqual(got, set(), found)
                else:
                    self.assertTrue(set(expected) <= got, (expected, found))
                    self.assertTrue({kind for kind, _ in got} <= {kind for kind, _ in expected}, found)

    def test_the_guide_word_lists_equal_the_script_lists(self):
        import re
        namespace = load_recipe()
        guide = (INSTALL / "references/guides/controlled-writing.md").read_text(encoding="utf-8")
        for label, language in (("English", "en"), ("Spanish", "es")):
            line = next(row for row in guide.splitlines() if row.startswith(label + ": "))
            phrases = re.findall(r"`([^`]+)`", line)
            self.assertGreater(len(phrases), 10)
            for phrase in phrases:
                with self.subTest(language=language, phrase=phrase):
                    found = namespace["findings"]("We note %s.\n" % phrase, language)
                    self.assertEqual([item["kind"] for item in found], ["vague"], found)
            for pattern in namespace["VAGUE"][language]:
                with self.subTest(language=language, pattern=pattern):
                    self.assertTrue(any(re.fullmatch(pattern, phrase, re.IGNORECASE) for phrase in phrases))

    def test_the_guide_passes_its_own_check(self):
        findings = load_recipe()["findings"]
        guide = (INSTALL / "references/guides/controlled-writing.md").read_text(encoding="utf-8")
        self.assertEqual(findings(guide, "en"), [])


if __name__ == "__main__":
    unittest.main()
