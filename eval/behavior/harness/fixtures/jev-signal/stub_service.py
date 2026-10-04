"""A local stand-in for the System One endpoint, and a builder for a synthetic cohort workspace.

Nothing here reaches a network beyond the loopback interface. The stub answers like the real API: it
checks the bearer header, reads ``model``, ``state`` and ``questions``, and answers each question from a
marker word in the participant's final message. The builder copies a protocol fixture cohort and gives each
episode a stream-json transcript and a synthetic scenario tree, so the signal module has every input it reads.
"""
import hashlib
import http.server
import json
import ssl
import threading
from pathlib import Path

MODEL = 'jev-1.13.0'
SHARED_SENTENCE = 'the quick brown fox jumps over the lazy dog'
ZERO = '0' * 64

# marker -> (failure cause choice, its confidence, level probabilities for every score question)
MARKERS = {
    'mark-fell': ('obligation-dropped', 0.9, {'0': 0.7, '1': 0.2, '2': 0.1}),
    'mark-ok': ('none', 0.85, {'0': 0.1, '1': 0.2, '2': 0.7}),
    'mark-dissent': ('instruction-ignored', 0.6, {'0': 0.2, '1': 0.6, '2': 0.2}),
    'mark-strong': ('instruction-ignored', 0.99, {'0': 0.3, '1': 0.4, '2': 0.3}),
    'mark-blind': ('none', 0.8, {'0': 0.2, '1': 0.3, '2': 0.5}),
}
CAUSES = ('count-reset', 'count-unread', 'cap-exceeded', 'effect-repeated', 'effect-unobserved',
          'obligation-dropped', 'closure-claimed', 'archive-overread', 'instruction-ignored', 'other', 'none')


def marker_of(state):
    text = str((state or {}).get('final_message', ''))
    for name in MARKERS:
        if name in text:
            return name
    return 'mark-ok'


def answer(name, question, marker):
    cause, confidence, levels = MARKERS[marker]
    if question.get('type') == 'choice':
        rest = (1 - confidence) / (len(CAUSES) - 1)
        return {'type': 'choice', 'choice': cause, 'confidence': confidence,
                'probabilities': {c: (confidence if c == cause else round(rest, 6)) for c in CAUSES}}
    top = max(levels.values())
    return {'type': 'score', 'score': round(sum(int(k) * v for k, v in levels.items()), 4), 'confidence': top,
            'legend': {k: 'level ' + k for k in levels}, 'probabilities': dict(levels)}


class Stub:
    """Serve the endpoint on loopback. ``tls`` is a (certificate, key) pair of paths for an https stub."""

    def __init__(self, key, model=MODEL, status=200, echo=None, tls=None, usage=(120, 30), redirect=None):
        self.key, self.model, self.status, self.echo, self.tls, self.usage = key, model, status, echo, tls, usage
        self.redirect = redirect
        self.requests = []
        stub = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                length = int(self.headers.get('Content-Length') or 0)
                body = json.loads(self.rfile.read(length) or b'{}')
                stub.requests.append({'authorized': self.headers.get('Authorization') == 'Bearer ' + stub.key,
                                      'path': self.path, 'body': body})
                if stub.status != 200:
                    self.send_response(stub.status)
                    if stub.redirect:
                        self.send_header('Location', stub.redirect)
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                marker = marker_of(body.get('state'))
                answers = {name: answer(name, q, marker) for name, q in (body.get('questions') or {}).items()}
                if stub.echo:
                    answers[next(iter(answers))]['note'] = stub.echo
                payload = json.dumps({'model': stub.model, 'answers': answers,
                                      'usage': {'input_tokens': stub.usage[0], 'output_tokens': stub.usage[1]}}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        Handler.do_GET = Handler.do_POST
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        if tls:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(tls[0], tls[1])
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self):
        return '%s://127.0.0.1:%d/v1/systemone' % ('https' if self.tls else 'http', self.server.server_address[1])

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def seal(manifest):
    body = {k: v for k, v in manifest.items() if k != 'seal_sha256'}
    return sha_bytes(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def transcript(final_message, commands):
    events = [{'type': 'system', 'subtype': 'init'}]
    for index, (name, given) in enumerate(commands):
        events.append({'type': 'assistant', 'message': {'content': [
            {'type': 'tool_use', 'id': 'call-%d' % index, 'name': name, 'input': given}]}})
        events.append({'type': 'user', 'message': {'content': [
            {'type': 'tool_result', 'tool_use_id': 'call-%d' % index, 'content': 'RESULT TEXT NEVER SENT'}]}})
    events.append({'type': 'result', 'subtype': 'success', 'result': final_message})
    return ''.join(json.dumps(event) + '\n' for event in events)


def build_workspace(root, fixture_cohort, markers, split='development', quote=(), tools=None):
    """Write cohort/, evidence/ and repo/eval/scenarios under root from a protocol fixture cohort.

    markers maps an episode id to a MARKERS name; quote lists episode ids whose final message repeats a
    sentence that the scenario's input also holds. Returns a dict of the paths."""
    root = Path(root)
    cohort, evidence, repo = root / 'cohort', root / 'evidence', root / 'repo'
    cohort.mkdir(parents=True)
    manifest = json.loads((Path(fixture_cohort) / 'manifest.json').read_text(encoding='utf-8'))
    for variant in manifest['variants']:
        variant['split'] = split
    manifest['seal_sha256'] = seal(manifest)
    (cohort / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    lines = []
    for line in (Path(fixture_cohort) / 'episodes.jsonl').read_text(encoding='utf-8').splitlines():
        record = json.loads(line)
        record['split'] = split
        lines.append(record)
    previous = ZERO
    out = []
    for record in lines:
        record['prev_sha256'] = previous
        text = json.dumps(record, sort_keys=True, separators=(',', ':'))
        out.append(text)
        previous = sha_bytes(text.encode())
    (cohort / 'episodes.jsonl').write_text('\n'.join(out) + '\n', encoding='utf-8')
    for record in lines:
        message = 'Final report for %s with %s.' % (record['episode_id'], markers.get(record['episode_id'], 'mark-ok'))
        if record['episode_id'] in quote:
            message += ' It said that ' + SHARED_SENTENCE + ' during the run.'
        folder = evidence / record['episode_id'] / 'sessions' / '01'
        folder.mkdir(parents=True)
        calls = (tools or {}).get(record['episode_id']) or [('Bash', {'command': 'ls -la'}), ('Bash', {'command': 'python3 -m unittest'})]
        (folder / 'stdout.jsonl').write_text(transcript(message, calls), encoding='utf-8')
    for variant in manifest['variants']:
        base = repo / 'eval' / 'scenarios' / variant['scenario_id'] / 'variants' / variant['variant_id']
        (base / 'input').mkdir(parents=True)
        (base / 'input' / 'notes.txt').write_text('Header line. ' + SHARED_SENTENCE + ' and more text.\n', encoding='utf-8')
        (base / 'GROUND-TRUTH.md').write_text('The answer sheet says other things entirely.\n', encoding='utf-8')
    return {'cohort': cohort, 'evidence': evidence, 'repo': repo, 'manifest': manifest, 'records': lines}
