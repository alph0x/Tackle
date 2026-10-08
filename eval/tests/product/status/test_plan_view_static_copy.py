"""A plan view that cannot refresh itself says so, and never suggests a server.

The shipped recipe writes a page for a small fixture; the page's own controller runs on its own markup in the
minimal DOM (plan_view_dom.js) with a scripted protocol and scripted stamp loads. The oracles cover the notice
element (hidden by default, its own element outside the freshness line and the print reports), its display
rule (protocol check once at start, two consecutive failed stamp loads, a later success), its texts (page
language, no server suggestion), the live-producer page and a mutation that never toggles the notice. Real
browser rendering, the host's snapshot view and real stamp loading are not observed.
"""
import re
import tempfile
import unittest

from plan_view_dom import run_scenario
from test_plan_selection import fixture
from test_plan_view import run_recipe

NOTICE_ID = 'plan-static-copy'

HELPERS = r"""
const notice = (env) => env.one('#plan-static-copy');
const start = (options) => {
  options = options || {};
  // The shared DOM has no lang property, removeChild or interval capture; add them to its element prototype.
  const proto = Object.getPrototypeOf(load().root);
  if (!('lang' in proto)) { Object.defineProperty(proto, 'lang', { get() { return this.getAttribute('lang') || ''; } }); }
  if (!proto.removeChild) {
    proto.removeChild = function (node) { const i = this.childNodes.indexOf(node); if (i >= 0) { this.childNodes.splice(i, 1); node.parentNode = null; } return node; };
  }
  // The harness loads under file:; run the shipped controller again on the same page under the scripted protocol.
  const env = load();
  env.intervals = [];
  env.window.setInterval = (fn) => { env.intervals.push(fn); return 1; };
  if (options.protocol !== undefined) { env.location.protocol = options.protocol; }
  vm.runInContext(env.scripts.controller, env.context);
  env.tick = () => env.intervals[env.intervals.length - 1]();
  env.pending = () => env.root.children.filter((c) => c.tagName === 'script');
  env.fail = () => { const s = env.pending().pop(); s.onerror(); };
  env.succeed = () => { const s = env.pending().pop(); s.onload(); };
  return env;
};
"""

SEQUENCE = r"""
const env = start({ protocol: 'file:' });
assert.ok(notice(env).hidden, 'hidden before any check');
env.tick(); env.fail();
assert.ok(notice(env).hidden, 'one failed load is not enough');
env.tick(); env.fail();
assert.ok(!notice(env).hidden, 'two consecutive failures show the notice');
assert.ok(/does not update itself/.test(notice(env).textContent));
env.tick(); env.succeed();
assert.ok(notice(env).hidden, 'a later success hides it');
env.tick(); env.fail();
env.tick(); env.succeed();
env.tick(); env.fail();
assert.ok(notice(env).hidden, 'failure, success, failure is not two in a row');
env.tick(); env.fail();
assert.ok(!notice(env).hidden);
"""


def render(lang=None, live=False):
    with tempfile.TemporaryDirectory() as tmp:
        result, out = run_recipe(tmp, fixture(), 'static-copy')
        assert result.returncode == 0, result.stdout + result.stderr
        page = out.read_text(encoding='utf-8')
    if lang:
        page = re.sub(r'<html lang="[^"]*"', '<html lang="%s"' % lang, page, count=1)
    if live:
        page = page.replace('<meta name="tackle-file-revision"', '<meta name="tackle-live-revision" content="r1"><meta name="tackle-file-revision"', 1)
    return page


class PlanViewStaticCopyTests(unittest.TestCase):
    page = None

    @classmethod
    def setUpClass(cls):
        cls.page = render()

    def run_js(self, code, page=None):
        result = run_scenario(page or self.page, HELPERS + code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, 'OK', result.stderr)

    def test_the_notice_is_its_own_hidden_element_outside_the_freshness_line_and_the_print_reports(self):
        self.assertEqual(len(re.findall(r'id="%s"' % NOTICE_ID, self.page)), 1)
        tag = re.search(r'<[^>]*id="%s"[^>]*>' % NOTICE_ID, self.page).group(0)
        self.assertRegex(tag, r'\bhidden\b')
        self.assertIn('data-en="', tag)
        self.assertIn('data-es="', tag)
        self.assertRegex(self.page, r'@media print\{[^@]*\.static-copy\{display:none!important\}')
        self.run_js(r"""
const env = start();
const el = notice(env);
assert.ok(el && el.hidden);
assert.ok(!el.closest('.freshness') && !el.closest('#plan-freshness') && !el.closest('.print-reports'));
assert.strictEqual(el.parentNode, env.document.body, 'a direct body child, so the print rule hides it');
assert.ok(env.one('#plan-freshness'), 'the freshness line stays separate');
""")

    def test_an_address_that_is_not_file_http_or_https_shows_the_notice_from_the_first_check(self):
        self.run_js(r"""
for (const protocol of ['data:', 'about:', 'blob:', '']) {
  const env = start({ protocol });
  assert.ok(!notice(env).hidden, 'shown at start under ' + JSON.stringify(protocol) + ' without a poll');
  assert.ok(notice(env).textContent.length > 20);
}
for (const protocol of ['file:', 'http:', 'https:']) {
  const env = start({ protocol });
  assert.ok(notice(env).hidden, 'hidden at start under ' + protocol);
}
""")

    def test_two_consecutive_failed_stamp_loads_show_the_notice_and_a_success_hides_it(self):
        self.run_js(SEQUENCE)

    def test_a_skipped_tick_is_not_a_failed_load(self):
        self.run_js(r"""
const env = start({ protocol: 'file:' });
env.tick();
env.tick();
env.tick();
assert.strictEqual(env.pending().length, 1, 'a tick while a load is pending starts nothing');
env.fail();
assert.ok(notice(env).hidden, 'skipped ticks count for nothing: one real failure');
env.document.hidden = true;
env.tick();
assert.strictEqual(env.pending().length, 0, 'a hidden tab starts no load');
env.document.hidden = false;
env.tick(); env.fail();
assert.ok(!notice(env).hidden, 'the second real failure shows it');
""")

    def test_the_live_producer_page_never_shows_the_notice(self):
        self.run_js(r"""
const env = start({ protocol: 'data:' });
assert.ok(notice(env).hidden);
assert.strictEqual(env.intervals.length, 0, 'the file view does not run on the live page');
""", page=render(live=True))

    def test_the_text_follows_the_page_language_and_suggests_no_server(self):
        self.run_js(r"""
const env = start({ protocol: 'data:' });
const english = notice(env).textContent;
assert.ok(/plan-view\.html/.test(english) && /browser/.test(english));
assert.ok(!/server|servidor|localhost|http\.server/i.test(english));
""")
        self.run_js(r"""
const env = start({ protocol: 'data:' });
const spanish = notice(env).textContent;
assert.ok(/plan-view\.html/.test(spanish) && /navegador/.test(spanish) && !/does not/.test(spanish));
assert.ok(!/server|servidor|localhost|http\.server/i.test(spanish));
""", page=render(lang='es'))
        tag = re.search(r'<[^>]*id="%s"[^>]*>' % NOTICE_ID, self.page).group(0)
        self.assertIsNone(re.search(r'server|servidor|localhost|http\.server', tag, re.I))

    def test_a_script_that_never_shows_the_notice_fails_the_scenarios(self):
        mutated = self.page.replace('copyNotice.hidden = !on;', '', 1)
        self.assertTrue(mutated != self.page, 'the mutation must change the shipped script')
        result = run_scenario(mutated, HELPERS + SEQUENCE)
        self.assertNotEqual(result.returncode, 0, 'a notice that is never toggled must not pass')


if __name__ == '__main__':
    unittest.main()
