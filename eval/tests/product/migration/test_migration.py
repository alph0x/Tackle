import re
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
import sys
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402
INSTALL = current_root(ROOT)


def heading_fragment(line):
    return re.sub(r"[^a-z0-9 -]", "", line.lower()).strip().replace(" ", "-")


class MigrationContract(unittest.TestCase):
    def test_public_surface_has_two_actions_and_readonly_status(self):
        skill = (INSTALL / "SKILL.md").read_text()
        readme = (ROOT / "README.md").read_text()
        for text in (skill, readme):
            self.assertIn("PLAN", text)
            self.assertIn("RUN", text)
            self.assertIn("STATUS", text)
            self.assertNotIn("candidate protocol 8.0 is unpublished", text)
        version = re.search(r"^\*\*Tackle ([0-9]+\.[0-9]+\.[0-9]+)\*\*", skill, re.MULTILINE)
        self.assertIsNotNone(version)
        self.assertIn("Tackle " + version.group(1), readme)
        self.assertIn("`run --one`", skill)
        invocation = (INSTALL / "references/guides/invocation.md").read_text()
        self.assertIn("/tackle-run --one", invocation)
        self.assertIn("aliases", skill)
        terminology = (INSTALL / "references/terminology.md").read_text()
        self.assertIn("retired in 9.0", terminology)
        self.assertNotIn("public surface at eight commands", skill)

    def test_status_has_no_log_write_exception(self):
        status = (INSTALL / "references/guides/status.md").read_text()
        self.assertIn("never executes a task or edits source, task board,\nhistory", status)
        self.assertIn("Only an explicit handoff request may write", status)
        self.assertNotIn("only write allowed is an optional `log.md` entry", status)
        self.assertIn("STATUS never archives history or appends a status event", status)

    def test_aliases_preserve_query_and_execution_intent(self):
        skill = (INSTALL / "SKILL.md").read_text()
        terminology = (INSTALL / "references/terminology.md").read_text()
        self.assertIn("`implement` | RUN", terminology)
        self.assertIn("`ground`, `trace`, `drill` | PLAN validation", terminology)
        self.assertIn("`pulse` | STATUS", terminology)
        self.assertIn("`handoff` | STATUS `--handoff`", terminology)
        self.assertIn("current STATUS request words, not retiring aliases", terminology)
        self.assertIn("explicit resume request that also states execution intent", skill)


    def test_heading_fragment_excludes_heading_separator(self):
        headings = {heading_fragment(line) for line in [
            "## Execute canonical lint faithfully", "# Prepare once, then capture"]}
        self.assertIn("execute-canonical-lint-faithfully", headings)
        self.assertIn("prepare-once-then-capture", headings)
        self.assertNotIn("-execute-canonical-lint-faithfully", headings)
        self.assertNotIn("missing-heading", headings)

    def test_install_is_markdown_only_and_links_resolve(self):
        with tempfile.TemporaryDirectory() as temp:
            install = Path(temp) / "skill"
            install.mkdir()
            shutil.copy2(INSTALL / "SKILL.md", install / "SKILL.md")
            shutil.copytree(INSTALL / "references", install / "references")
            files = list(install.rglob("*"))
            self.assertTrue(files)
            self.assertTrue(all(p.is_dir() or p.suffix == ".md" for p in files))
            text = "\n".join(p.read_text() for p in install.rglob("*.md"))
            self.assertNotIn("docs/plans/tackle-plan-run", text)
            for source in install.rglob("*.md"):
                for link in re.findall(r"\]\(([^)]+)\)", source.read_text()):
                    target, _, fragment = link.partition("#")
                    if not target or target.startswith(("http:", "https:", "mailto:")):
                        continue
                    if "<" in target or "{{" in target or target.startswith("docs/plans/"):
                        continue
                    destination = (source.parent / target).resolve()
                    if destination.is_file() and fragment:
                        headings = {heading_fragment(line)
                                    for line in destination.read_text().splitlines() if line.startswith("#")}
                        headings.update(re.findall(r'<a id="([^"]+)"', destination.read_text()))
                        self.assertIn(fragment.lower(), headings, link)
                    elif target.startswith(("references/", "guides/", "../")):
                        self.assertTrue(destination.is_file(), link)


if __name__ == "__main__":
    unittest.main()
