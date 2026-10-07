"""The actual local producer refreshes public inputs and serves an honest bounded snapshot.

These cases execute both shipped recipes on throwaway public workspaces. HTTP requests go through
the actual BaseHTTPRequestHandler with an in-memory socket, never a listener or a native browser.
The oracle covers source changes, transactional failure/recovery and route/Host boundaries; it does
not establish browser rendering, polling or native export behavior.
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import tempfile
import unittest
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
LIVE_RECIPE = REPO / 'skills/tackle/references/recipes/plan-view-live.md'


def helper_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPERS = helper_module('plan_live_view_helpers', 'test_plan_view.py')
MAP_HELPERS = helper_module('plan_live_map_helpers', 'test_architecture_map.py')


class PageMetadata(HTMLParser):
    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.feed(page)

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if tag == 'meta' and 'name' in attrs:
            self.meta[attrs['name']] = attrs.get('content', '')


class MemorySocket:
    """Only the stream/socket methods used by StreamRequestHandler; no socket is opened."""
    def __init__(self, request):
        self.request = io.BytesIO(request)
        self.response = io.BytesIO()

    def makefile(self, *_args, **_kwargs):
        return self.request

    def sendall(self, data):
        self.response.write(data)


def request(live, state, path='/', host='127.0.0.1:8787'):
    message = ('GET %s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host)).encode('ascii')
    connection = MemorySocket(message)
    server = SimpleNamespace(state=state, server_address=('127.0.0.1', 8787),
                             server_name='127.0.0.1', server_port=8787)
    live['Handler'](connection, ('127.0.0.1', 50001), server)
    head, body = connection.response.getvalue().split(b'\r\n\r\n', 1)
    status, raw_headers = head.split(b'\r\n', 1)
    headers = BytesParser().parsebytes(raw_headers + b'\r\n\r\n')
    return int(status.split()[1]), headers, body


def island(page):
    match = re.search(r'<script[^>]*\bid="plan-view-data"[^>]*>(.*?)</script>', page, re.S)
    if match is None:
        raise AssertionError('the actual page has no canonical data island')
    return json.loads(match.group(1))


class PlanLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = MAP_HELPERS.fenced_source(LIVE_RECIPE)
        cls.live = {'__name__': 'plan_live_recipe', '__file__': str(LIVE_RECIPE)}
        exec(compile(source, str(LIVE_RECIPE), 'exec'), cls.live)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name).resolve() / 'project'
        self.workspace = self.project / 'docs/plans/live'
        self.template = self.project / 'presentation/plan-view.template.md'
        self.fixed_ns = 1800000000000000000
        for name, text in HELPERS.workspace_files().items():
            self.write(name, text)
        self.template.parent.mkdir(parents=True)
        self.template.write_bytes(HELPERS.TEMPLATE.read_bytes())
        os.utime(self.template, ns=(self.fixed_ns, self.fixed_ns))
        map_recipe = self.template.parent / 'recipes/architecture-map.md'
        map_recipe.parent.mkdir()
        map_recipe.write_bytes(MAP_HELPERS.MAP_RECIPE.read_bytes())
        self.recipe_path = self.template.parent / 'recipes/plan-view.md'
        self.recipe_path.write_bytes(HELPERS.RECIPE.read_bytes())
        os.utime(self.recipe_path, ns=(self.fixed_ns, self.fixed_ns))
        self.recipe = self.live['load_plan_recipe'](self.recipe_path)

    def write(self, name, text):
        path = self.workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        os.utime(path, ns=(self.fixed_ns, self.fixed_ns))
        return path

    def state(self, map_base=None):
        return self.live['LivePage'](self.recipe, self.template, self.workspace, map_base, 'all')

    def fresh(self, state):
        status, headers, body = request(self.live, state)
        self.assertEqual(status, 200, body)
        self.assertEqual(headers.get('X-Tackle-Live'), '1')
        self.assertEqual(headers.get('Cache-Control'), 'no-store')
        revision = headers.get('X-Tackle-Revision', '')
        self.assertRegex(revision, r'^[0-9a-f]{64}$')
        page = body.decode('utf-8')
        self.assertEqual(PageMetadata(page).meta.get('tackle-live-revision'), revision)
        status, health_headers, health_body = request(self.live, state, '/health')
        self.assertEqual(status, 200, health_body)
        health = json.loads(health_body)
        self.assertTrue(health['ok'])
        self.assertEqual(health['revision'], revision)
        self.assertEqual(health_headers.get('X-Tackle-Live'), '1')
        self.assertEqual(health_headers.get('X-Tackle-Revision'), revision)
        return page, revision

    def test_same_timestamp_public_content_and_presentation_changes_refresh_the_actual_page(self):
        summary = {'outcomes': [{'title': 'Alpha', 'text': 'A public outcome.'}]}
        summary_path = self.write('view/summary.json', json.dumps(summary))
        state = self.state()
        page, previous = self.fresh(state)
        self.assertIn('Alpha', page)
        summary['outcomes'][0]['title'] = 'Bravo'
        self.write('view/summary.json', json.dumps(summary))
        self.assertEqual(summary_path.stat().st_mtime_ns, self.fixed_ns)
        page, revision = self.fresh(state)
        self.assertIn('Bravo', page)
        self.assertNotEqual(revision, previous, 'same-size, same-time content changes must refresh')
        previous = revision

        board = (self.workspace / 'task-board.md').read_text(encoding='utf-8')
        self.write('task-board.md', board.replace('| In progress |', '| Complete |', 1))
        page, revision = self.fresh(state)
        tasks = {task['id']: task['status'] for task in island(page)['tasks']}
        self.assertEqual(tasks[HELPERS.task_id(2)], 'Complete')
        self.assertNotEqual(revision, previous)
        previous = revision

        brief = 'tasks/%s.md' % HELPERS.task_id(2)
        text = (self.workspace / brief).read_text(encoding='utf-8')
        self.write(brief, text.replace(HELPERS.req_id(2), HELPERS.req_id(1)))
        page, revision = self.fresh(state)
        self.assertIn(HELPERS.task_id(2), island(page)['requirements'][HELPERS.req_id(1)])
        self.assertNotEqual(revision, previous, 'brief content affects canonical requirement coverage')
        previous = revision

        template = self.template.read_text(encoding='utf-8')
        self.template.write_text(template.replace('</main>', '<p>template-refresh-sentinel</p></main>'),
                                 encoding='utf-8')
        os.utime(self.template, ns=(self.fixed_ns, self.fixed_ns))
        page, revision = self.fresh(state)
        self.assertIn('template-refresh-sentinel', page)
        self.assertNotEqual(revision, previous)
        previous = revision

        agents = (self.workspace / 'AGENTS.md').read_text(encoding='utf-8')
        self.write('AGENTS.md', agents.replace('9.1.0', '9.1.1'))
        page, revision = self.fresh(state)
        self.assertIn('9.1.1', page)
        self.assertNotEqual(revision, previous, 'recorded methodology is a public rendering input')
        previous = revision

        recipe_source = self.recipe_path.read_text(encoding='utf-8')
        code, fence, tail = recipe_source.rpartition('\n```')
        self.assertTrue(fence, 'the copied shipped recipe has a closing source fence')
        code += ("\n\n_original_fill = fill\ndef fill(template, values):\n"
                 "    return _original_fill(template, values) + '<!--recipe-refresh-sentinel-->'\n")
        self.recipe_path.write_text(code + fence + tail, encoding='utf-8')
        os.utime(self.recipe_path, ns=(self.fixed_ns, self.fixed_ns))
        page, revision = self.fresh(state)
        self.assertIn('<!--recipe-refresh-sentinel-->', page,
                      'source freshness must consume the changed recipe, not only hash its bytes')
        self.assertNotEqual(revision, previous)
        result, output = HELPERS.run_recipe(self.temporary.name, HELPERS.workspace_files(), 'file-snapshot')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        snapshot = output.read_text(encoding='utf-8')
        self.assertNotIn('tackle-live-revision', PageMetadata(snapshot).meta,
                         'ordinary file generation must not claim live freshness')

    def test_actual_handler_serves_only_declared_routes_and_rejects_foreign_hosts(self):
        state = self.state()
        self.fresh(state)
        for path in ('/?x=1', '/health?x=1', '/other', '/plan.md', '/%2e%2e/plan.md'):
            with self.subTest(path=path):
                status, _headers, body = request(self.live, state, path)
                self.assertEqual(status, 404)
                self.assertNotIn(b'plan-view-data', body)
        for host in ('evil.example:8787', 'localhost.evil:8787', '127.0.0.1:9999',
                     '127.0.0.1:8787@evil.example'):
            with self.subTest(host=host):
                status, _headers, body = request(self.live, state, host=host)
                self.assertIn(status, (400, 403))
                self.assertNotIn(b'plan-view-data', body)

    def test_failed_or_escaping_inputs_keep_last_good_content_unhealthy_and_recovery_clears_error(self):
        state = self.state()
        page, revision = self.fresh(state)
        brief = self.workspace / ('tasks/%s.md' % HELPERS.task_id(2))
        original = brief.read_bytes()
        brief.unlink()
        status, headers, body = request(self.live, state)
        self.assertIn(status, (200, 503))
        self.assertEqual(headers.get('X-Tackle-Live'), '0')
        self.assertEqual(headers.get('X-Tackle-Revision'), revision)
        self.assertEqual(island(body.decode('utf-8')), island(page))
        status, _headers, health_body = request(self.live, state, '/health')
        self.assertEqual(status, 503)
        self.assertFalse(json.loads(health_body)['ok'])
        brief.write_bytes(original)
        os.utime(brief, ns=(self.fixed_ns, self.fixed_ns))
        _page, recovered = self.fresh(state)
        self.assertEqual(recovered, revision, 'restoring identical source content restores the same revision')

        outside = self.project / 'outside-public-fixture.json'
        outside.write_text('{"objective":"outside-workspace-secret-sentinel"}', encoding='utf-8')
        summary = self.workspace / 'summary.json'
        summary.symlink_to(outside)
        status, headers, body = request(self.live, state)
        self.assertIn(status, (200, 503))
        self.assertEqual(headers.get('X-Tackle-Live'), '0')
        self.assertNotIn(b'outside-workspace-secret-sentinel', body)
        status, _headers, health_body = request(self.live, state, '/health')
        self.assertEqual(status, 503)
        self.assertFalse(json.loads(health_body)['ok'])
        summary.unlink()
        self.fresh(state)

        unselected = self.workspace / 'notes/unselected.md'
        unselected.parent.mkdir()
        unselected.symlink_to(outside)
        board = (self.workspace / 'task-board.md').read_text(encoding='utf-8')
        self.write('task-board.md', board.replace('| v |', '| `notes/unselected.md` |', 1))
        safe_page, _revision = self.fresh(state)
        self.assertNotIn('outside-workspace-secret-sentinel', safe_page,
                         'a verification-cell backtick is not a selected brief input')

        (self.workspace / 'plan.md').unlink()
        initial = self.state()
        with self.assertRaises(Exception):
            initial.refresh()
        status, headers, body = request(self.live, initial)
        self.assertEqual(status, 503)
        self.assertEqual(headers.get('X-Tackle-Live'), '0')
        self.assertNotIn(b'plan-view-data', body)
        status, _headers, health_body = request(self.live, initial, '/health')
        self.assertEqual(status, 503)
        self.assertFalse(json.loads(health_body)['ok'])

    def test_explicit_project_map_outside_workspace_is_a_valid_public_input_and_refreshes(self):
        base = MAP_HELPERS.base_map()
        map_path = self.project / '.tackle/map/architecture.json'
        map_path.parent.mkdir(parents=True)
        map_path.write_text(json.dumps(base), encoding='utf-8')
        os.utime(map_path, ns=(self.fixed_ns, self.fixed_ns))
        state = self.state(map_path)
        page, revision = self.fresh(state)
        self.assertEqual(set(island(page)['map']['today']), {item['id'] for item in base['components']})
        base['components'][0]['title'] = 'Updated project map component'
        map_path.write_text(json.dumps(base), encoding='utf-8')
        os.utime(map_path, ns=(self.fixed_ns, self.fixed_ns))
        page, updated = self.fresh(state)
        self.assertIn('Updated project map component', page)
        self.assertNotEqual(updated, revision)

        servers = []

        class MemoryServer:
            def __init__(self, address, handler):
                self.server_address = address
                self.handler = handler
                self.closed = False
                servers.append(self)

            def serve_forever(self):
                raise KeyboardInterrupt

            def server_close(self):
                self.closed = True

        argv = ['plan-view-live.py', '--template', str(self.template), '--recipe', str(self.recipe_path), '--map', str(map_path),
                '--port', '8787', str(self.workspace)]
        with mock.patch.object(self.live['http'].server, 'ThreadingHTTPServer', MemoryServer), \
                mock.patch.object(self.live['sys'], 'argv', argv), \
                contextlib.redirect_stdout(io.StringIO()):
            self.live['main']()
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0].server_address, ('127.0.0.1', 8787))
        self.assertIs(servers[0].handler, self.live['Handler'])
        self.assertTrue(servers[0].closed)
        self.assertIn('Updated project map component', servers[0].state.page)


if __name__ == '__main__':
    unittest.main()
