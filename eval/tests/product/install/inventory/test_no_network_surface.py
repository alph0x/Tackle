"""The install carries no network client, no third-party endpoint and no home-directory lookup.

Guarantee: every `.md` and `.py` file under the installed skill is free of a third-party API endpoint
(`api.typesafe.ai`, or any `http(s)://host` URL inside a `.py` file other than the allowlisted entries
below), a home lookup (`Path.home(`, `expanduser(`, `~/.codex`, `~/.claude/projects`, `$HOME/`) and, in a
`.py` file, any import of socket, http, urllib, requests, ftplib or smtplib. A negative fixture plants
each pattern in a scratch tree and proves the scan reports it, so a scan that silently matches nothing
fails here too.
"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from maintaining.install_root import current_root  # noqa: E402

INSTALL = current_root(ROOT)

ANY_FILE = {
    'third-party endpoint': re.compile(r'api\.typesafe\.ai'),
    'Path.home': re.compile(r'Path\.home\('),
    'expanduser': re.compile(r'expanduser\('),
    'codex home': re.compile(r'~/\.codex'),
    'claude projects home': re.compile(r'~/\.claude/projects'),
    'HOME variable path': re.compile(r'\$HOME/'),
}
PY_ONLY = {
    'URL in a script': re.compile(r'https?://[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+'),
    'network import': re.compile(r'^\s*(?:import|from)\s+(?:socket|http|urllib|requests|ftplib|smtplib)\b', re.M),
}
# Each entry: (path relative to the install root, exact line text, reason). Nothing else is excused.
ALLOWED = {
    ('scripts/plan_view.py', "REPO_URL = 'https://github.com/alph0x/Tackle'"):
        'A documented link string the plan view prints into the page footer; the script never opens it.',
}


def scan(root):
    """[(relative path, line number, label)] for every match under root."""
    found = []
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix not in ('.md', '.py'):
            continue
        relative = path.relative_to(root).as_posix()
        patterns = dict(ANY_FILE, **(PY_ONLY if path.suffix == '.py' else {}))
        for number, line in enumerate(path.read_text(encoding='utf-8').split('\n'), 1):
            if (relative, line.strip()) in ALLOWED:
                continue
            for label, pattern in patterns.items():
                if pattern.search(line):
                    found.append((relative, number, label))
    return found


class NoNetworkSurface(unittest.TestCase):
    def test_the_install_has_no_endpoint_home_lookup_or_network_import(self):
        self.assertEqual(scan(INSTALL), [])

    def test_every_allowlisted_line_still_exists(self):
        for relative, line in ALLOWED:
            with self.subTest(path=relative):
                lines = [text.strip() for text in (INSTALL / relative).read_text(encoding='utf-8').split('\n')]
                self.assertIn(line, lines)

    def test_each_pattern_is_caught_in_a_planted_tree(self):
        planted = {
            'guide.md': ['call https://api.typesafe.ai/v1', 'read ~/.codex/sessions', 'see ~/.claude/projects/x',
                         'cd $HOME/.agents'],
            'scripts/probe.py': ['base = Path.home() / "x"', 'p = Path(a).expanduser()', 'import socket',
                                 'from urllib import request', 'import http.client', 'import requests',
                                 'import ftplib', 'from smtplib import SMTP', 'URL = "https://example.org/api"',
                                 "REPO_URL = 'https://github.com/alph0x/Tackle'"],
        }
        expected = {'third-party endpoint', 'codex home', 'claude projects home', 'HOME variable path',
                    'Path.home', 'expanduser', 'network import', 'URL in a script'}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative, lines in planted.items():
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                (root / relative).write_text('\n'.join(lines) + '\n', encoding='utf-8')
            found = scan(root)
        self.assertEqual({label for _, _, label in found}, expected)
        self.assertEqual(len([f for f in found if f[2] == 'network import']), 6)
        # The allowlist names a path inside the install, so a planted copy elsewhere is still reported.
        self.assertIn(('scripts/probe.py', 10, 'URL in a script'), found)
        # A Markdown link to a web page is documentation, not a script endpoint.
        self.assertNotIn('URL in a script', {label for path, _, label in found if path.endswith('.md')})


if __name__ == '__main__':
    unittest.main()
