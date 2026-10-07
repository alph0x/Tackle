"""Run the shipped plan-view controller against a generated page through the minimal DOM in plan_view_dom.js.

The page's own markup becomes the DOM and the page's own inline scripts run on it, so a check covers the
markup and the controller that ship together. The DOM implements events, classes, attributes and the
selectors the controller uses; it has no layout, so sizes are given by the scenario.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

HARNESS = Path(__file__).with_name('plan_view_dom.js')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root, self.stack = None, []

    def handle_starttag(self, tag, attrs):
        node = [tag, {name: value if value is not None else '' for name, value in attrs}, []]
        if self.stack:
            self.stack[-1][2].append(node)
        elif tag == 'html':
            self.root = node
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = [tag, {name: value if value is not None else '' for name, value in attrs}, []]
        if self.stack:
            self.stack[-1][2].append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self.stack and data:
            self.stack[-1][2].append(data)


def page_tree(page):
    builder = TreeBuilder()
    builder.feed(page)
    builder.close()
    assert builder.root is not None, 'the page has no html element'
    return builder.root


def page_scripts(page):
    found = {}
    for name, ident in (('controller', 'plan-view-controller'), ('client', 'plan-view-live-client')):
        match = re.search(r'<script id="%s">(.*?)</script>' % ident, page, re.S)
        assert match, 'the generated page has no %s script' % ident
        found[name] = match.group(1)
    return found


def node_binary():
    node = os.environ.get('TACKLE_NODE') or shutil.which('node')
    if node and not Path(node).is_file():
        node = shutil.which(node)
    assert node and Path(node).is_file(), 'an existing Node interpreter is required; do not skip controller checks'
    return node


def run_scenario(page, scenario, timeout=60):
    """Run a scenario (JavaScript using load(), assert and settle()) against the page; returns the finished process."""
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        (folder / 'tree.json').write_text(json.dumps(page_tree(page)), encoding='utf-8')
        (folder / 'scripts.json').write_text(json.dumps(page_scripts(page)), encoding='utf-8')
        (folder / 'scenario.js').write_text(scenario, encoding='utf-8')
        return subprocess.run([node_binary(), str(HARNESS), str(folder / 'tree.json'), str(folder / 'scripts.json'), str(folder / 'scenario.js')],
                              capture_output=True, text=True, timeout=timeout)
