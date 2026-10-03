"""The controlled-writing recipe judges fixture texts, and the shipped guide passes its own check."""
import ast
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
    text = (INSTALL / "references/recipes/controlled-writing.md").read_text(encoding="utf-8")
    parts = text.split("```python\n")
    assert len(parts) == 2, "the recipe holds exactly one fenced python block"
    source = parts[1].split("\n```")[0]
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & FORBIDDEN, "the recipe imports %s" % sorted(imported & FORBIDDEN)
    namespace = {"__name__": "controlled_writing"}
    exec(compile(source, "controlled-writing.md", "exec"), namespace)
    return namespace


class ControlledWriting(unittest.TestCase):
    def test_the_shipped_recipe_judges_fixture_texts(self):
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

    def test_the_guide_passes_its_own_check(self):
        findings = load_recipe()["findings"]
        guide = (INSTALL / "references/guides/controlled-writing.md").read_text(encoding="utf-8")
        self.assertEqual(findings(guide, "en"), [])


if __name__ == "__main__":
    unittest.main()
