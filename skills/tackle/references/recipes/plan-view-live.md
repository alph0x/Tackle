```python
import argparse
import contextlib
import datetime
import hashlib
import http.server
import io
import json
import re
import sys
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlsplit

FIXED_INPUTS = ('plan.md', 'task-board.md', 'decisions.md', 'questions.md', 'history.md', 'resource-usage.md',
                'summary.json', 'view/summary.json', 'export-summary.json', 'view/export-summary.json',
                'map-delta.json', 'AGENTS.md', 'readiness.md')


def recipe_code(path):
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    if not lines or lines[0] != '```python':
        raise ValueError('plan-view recipe must start with a Python fence')
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line == '```')
    except StopIteration as problem:
        raise ValueError('plan-view recipe fence is not closed') from problem
    return '\n'.join(lines[1:end]) + '\n'


def load_plan_recipe(path):
    namespace = {'__name__': 'plan_view_recipe', '__source_path': str(Path(path).resolve())}
    exec(compile(recipe_code(path), str(path), 'exec'), namespace)
    if not callable(namespace.get('main')):
        raise ValueError('plan-view recipe has no main entry point')
    return namespace


def inside(root, path):
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as problem:
        raise ValueError('a workspace input resolves outside the workspace') from problem
    return resolved


def declared_briefs(workspace):
    board = inside(workspace, workspace / 'task-board.md')
    if not board.is_file():
        return []
    text = board.read_text(encoding='utf-8')
    def cells(line):
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        return [part.strip().replace('\\|', '|') for part in re.split(r'(?<!\\)\|', line)]

    header_index = None
    columns = None
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.lstrip().startswith('|'):
            continue
        names = [part.lower() for part in cells(line)]
        if 'task' in names and 'brief' in names:
            header_index = index
            columns = {'task': names.index('task'), 'brief': names.index('brief')}
            break
    if header_index is None:
        return []
    paths = []
    for line in lines[header_index + 1:]:
        if not line.lstrip().startswith('|'):
            if paths:
                break
            continue
        parts = cells(line)
        if not parts or all(re.fullmatch(r':?-{3,}:?', part) for part in parts):
            continue
        if max(columns.values()) >= len(parts) or not re.fullmatch(r'T-\d+', parts[columns['task']]):
            continue
        raw = parts[columns['brief']]
        link = re.fullmatch(r'\[[^]]*\]\(([^)\s]+)\)', raw)
        code = re.fullmatch(r'`([^`]+)`', raw)
        raw = (link.group(1) if link else code.group(1) if code else raw).strip()
        if raw.startswith(('#', 'http://', 'https://')):
            continue
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = workspace / candidate
        paths.append(inside(workspace, candidate))
    return paths


def public_paths(workspace, template, recipe_path, map_base):
    paths = [inside(workspace, workspace / name) for name in FIXED_INPUTS]
    paths += declared_briefs(workspace)
    paths += [template.resolve(), (template.parent / 'recipes' / 'architecture-map.md').resolve()]
    if recipe_path is not None:
        paths.append(recipe_path.resolve())
    if map_base is not None:
        paths.append(map_base.resolve())
    return paths


def fingerprint(paths):
    digest = hashlib.sha256()
    for path in sorted(set(paths), key=str):
        digest.update(str(path).encode('utf-8'))
        if not path.exists():
            digest.update(b'\x00missing')
            continue
        if not path.is_file():
            raise ValueError('a declared public input is not a file')
        digest.update(path.read_bytes())
    return digest.hexdigest()


def render_once(recipe, template, workspace, map_base, map_scope):
    output = tempfile.NamedTemporaryFile(prefix='tackle-plan-view-', suffix='.html', delete=False)
    output_path = Path(output.name)
    output.close()
    argv = ['plan-view.py', '--template', str(template)]
    if map_base is not None:
        argv += ['--map', str(map_base), '--map-scope', map_scope]
    argv += [str(workspace), str(output_path)]
    old_argv = sys.argv
    stdout, stderr = io.StringIO(), io.StringIO()
    try:
        sys.argv = argv
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = recipe['main']()
        if code:
            detail = (stderr.getvalue() or stdout.getvalue()).strip()
            raise RuntimeError('plan-view refused to render%s' % (': ' + detail if detail else ''))
        return output_path.read_text(encoding='utf-8')
    finally:
        sys.argv = old_argv
        try:
            output_path.unlink()
        except FileNotFoundError:
            pass


class LivePage:
    def __init__(self, recipe, template, workspace, map_base, map_scope):
        self.recipe = recipe
        self.template = template
        source_path = recipe.get('__source_path')
        self.recipe_path = Path(source_path).resolve() if source_path else None
        self.workspace = workspace
        self.map_base = map_base
        self.map_scope = map_scope
        self.paths = None
        self.lock = threading.RLock()
        self.page = ''
        self.fingerprint_value = None
        self.updated = None
        self.error = None

    def refresh(self):
        with self.lock:
            try:
                self.paths = public_paths(self.workspace, self.template, self.recipe_path, self.map_base)
                current = fingerprint(self.paths)
                if current == self.fingerprint_value and self.page:
                    self.error = None
                    return self.page
                active_recipe = load_plan_recipe(self.recipe_path) if self.recipe_path is not None else self.recipe
                page = render_once(active_recipe, self.template, self.workspace, self.map_base, self.map_scope)
                if fingerprint(self.paths) != current:
                    raise RuntimeError('public inputs changed during render')
            except Exception:
                self.error = 'refresh failed'
                if not self.page:
                    raise
                return self.page
            self.recipe = active_recipe
            self.page = page
            self.fingerprint_value = current
            self.updated = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self.error = None
            return page

    def fresh(self):
        return bool(self.page) and self.error is None and self.fingerprint_value is not None

    def health(self):
        with self.lock:
            self.refresh()
            return dict(ok=self.fresh(), fresh=self.fresh(), updated=self.updated,
                        revision=self.fingerprint_value, error=self.error)


def revision_page(page, revision):
    if not revision:
        return page
    meta = '<meta name="tackle-live-revision" content="%s">' % revision
    return re.sub(r'(?i)(<head\b[^>]*>)', r'\1' + meta, page, count=1)


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'TackleLive/1'
    sys_version = ''

    def reject(self, code):
        body = b'not available'
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Tackle-Live', '0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        expected = '127.0.0.1:%d' % self.server.server_address[1]
        if self.headers.get('Host', '') != expected:
            return False
        if self.headers.get('Authorization') or self.headers.get('Transfer-Encoding'):
            return False
        length = self.headers.get('Content-Length')
        return length in (None, '0') and '#' not in self.path

    def do_GET(self):
        if not self.authorized():
            self.reject(400)
            return
        request = urlsplit(self.path)
        if request.query or request.fragment or request.path not in ('/', '/health'):
            self.reject(404)
            return
        state = self.server.state
        try:
            if request.path == '/health':
                payload = state.health()
                body = json.dumps(payload, ensure_ascii=True).encode('utf-8')
                content_type = 'application/json; charset=utf-8'
                code = 200 if payload['fresh'] else 503
            else:
                page = state.refresh()
                body = revision_page(page, state.fingerprint_value).encode('utf-8')
                content_type = 'text/html; charset=utf-8'
                code = 200 if state.fresh() else 503
        except Exception:
            body = b'{"ok":false,"fresh":false,"error":"refresh failed"}' if request.path == '/health' else b'plan view unavailable'
            content_type = 'application/json; charset=utf-8' if request.path == '/health' else 'text/plain; charset=utf-8'
            code = 503
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Tackle-Live', '1' if state.fresh() and code == 200 else '0')
        self.send_header('X-Tackle-Revision', state.fingerprint_value or '')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.reject(405)

    def do_POST(self):
        self.reject(405)

    def log_message(self, _format, *_args):
        return


def main():
    parser = argparse.ArgumentParser(description='Serve a loopback live plan view from declared workspace inputs.')
    parser.add_argument('--template', required=True)
    parser.add_argument('--recipe', required=True, help='absolute or cwd-relative path to the plan-view.md source recipe')
    parser.add_argument('--map', dest='map_base')
    parser.add_argument('--map-scope', choices=('all', 'changed'), default='all')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('workspace')
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    template = Path(args.template).expanduser().resolve()
    recipe_path = Path(args.recipe).expanduser().resolve()
    if not workspace.is_dir() or not template.is_file() or recipe_path.suffix != '.md' or not recipe_path.is_file() or not 0 < args.port < 65536:
        parser.error('workspace, template, plan-view.md recipe and port must be valid')
    raw_map = Path(args.map_base).expanduser().resolve() if args.map_base else None
    recipe = load_plan_recipe(recipe_path)
    try:
        state = LivePage(recipe, template, workspace, raw_map, args.map_scope)
        state.refresh()
    except Exception:
        print('live view unavailable', file=sys.stderr)
        return 2
    server = http.server.ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.state = state
    print('serving plan view on http://127.0.0.1:%d/' % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
```
