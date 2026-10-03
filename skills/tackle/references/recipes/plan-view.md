```python
import argparse
import datetime
import html
import json
import re
import sys
from pathlib import Path

REPO_URL = 'https://github.com/alph0x/Tackle'
DEFAULT_STATES = ['Draft', 'Ready to run', 'In progress', 'Checking', 'Complete', 'Blocked', 'Interrupted',
                  'Skipped', 'Unverifiable', 'Waiting on owner']
UI = {
    'en': dict(
        working='Working now', working_none='No session works on this plan right now.', plan_scope='The plan',
        run_scope='The run', live='Live', graph='How the work connects',
        graph_note='Each arrow points from a task to the work that needs it. Select a task to trace it.',
        graph_none='This plan has no task board, so the view shows no graph.', clear='Clear the trace',
        tasks='Tasks', all='All', needs='Needs', unblocks='Unblocks', nothing='nothing', requirements='Requirements',
        brief='Brief', trace_up='Trace what it needs', trace_down='Trace what it unblocks',
        coverage='Requirement coverage', req='Requirement', check='How it is checked', covered_by='Tasks',
        no_task='No task yet', snapshot='Latest snapshot', snapshot_none='No snapshot is recorded.',
        technical='Technical details', technical_note='Ids, raw statuses and the decision log.', task='Task',
        status='Status', verification='Verification', decisions='Decision log', decision='Decision', state='State',
        date='Date', made_with='Made with Tackle', built='Built', focused_note='This plan has no task board. The view shows its requirements and checks.',
        s_tasks='tasks', s_done='complete', s_reqs='requirements', s_decisions='decisions',
        summary='{done} of {total} tasks are complete. {covered} of {reqs} requirements have a task.',
        summary_focused='This plan has no task board. It lists {reqs} requirements.',
        roles={'executor': 'Doing the work', 'adversary': 'Independent review', 'readiness reviewer': 'Checking the plan is ready',
               'brief compiler': 'Preparing the task briefs', 'auditor': 'Independent audit'}),
    'es': dict(
        working='En marcha ahora', working_none='Ninguna sesión trabaja en este plan ahora.', plan_scope='El plan',
        run_scope='La ejecución', live='En curso', graph='Cómo se conecta el trabajo',
        graph_note='Cada flecha va de una tarea al trabajo que la necesita. Elige una tarea para seguir su traza.',
        graph_none='Este plan no tiene tablero de tareas, así que la vista no muestra grafo.', clear='Quitar la traza',
        tasks='Tareas', all='Todas', needs='Necesita', unblocks='Habilita', nothing='nada', requirements='Requisitos',
        brief='Brief', trace_up='Seguir lo que necesita', trace_down='Seguir lo que habilita',
        coverage='Cobertura de requisitos', req='Requisito', check='Cómo se comprueba', covered_by='Tareas',
        no_task='Sin tarea todavía', snapshot='Última instantánea', snapshot_none='No hay instantánea registrada.',
        technical='Detalle técnico', technical_note='Ids, estados crudos y el registro de decisiones.', task='Tarea',
        status='Estado', verification='Verificación', decisions='Registro de decisiones', decision='Decisión', state='Estado',
        date='Fecha', made_with='Hecho con Tackle', built='Generado', focused_note='Este plan no tiene tablero de tareas. La vista muestra sus requisitos y comprobaciones.',
        s_tasks='tareas', s_done='completas', s_reqs='requisitos', s_decisions='decisiones',
        summary='{done} de {total} tareas están completas. {covered} de {reqs} requisitos tienen tarea.',
        summary_focused='Este plan no tiene tablero de tareas. Lista {reqs} requisitos.',
        roles={'executor': 'Haciendo el trabajo', 'adversary': 'Revisión independiente', 'readiness reviewer': 'Revisando que el plan esté listo',
               'brief compiler': 'Preparando los briefs', 'auditor': 'Auditoría independiente'}),
}
STOP = {
    'en': 'the and of to is are in for with that on each it as by be this from or an at which'.split(),
    'es': 'el la los las de que y en un una para con se por del es al lo como cada su sus tareas plan'.split(),
}


def esc(value):
    return html.escape(str(value), quote=True)


def read(ws, name):
    path = ws / name
    return path.read_text(encoding='utf-8') if path.is_file() else ''


def language(plan):
    words = re.findall(r'[a-záéíóúñü]+', plan.lower())
    accents = len(re.findall(r'[áéíóúñü¿¡]', plan.lower()))
    score_en = sum(1 for w in words if w in STOP['en'])
    score_es = sum(1 for w in words if w in STOP['es']) + 2 * accents
    return 'es' if score_es > score_en else 'en'


def cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def parse_board(text, problems):
    flat = ' '.join(text.split())
    found = re.search(r'States:\s*([^.]*)\.', flat)
    states = [s.strip() for s in found.group(1).split(',') if s.strip()] if found else list(DEFAULT_STATES)
    rows = []
    for line in text.splitlines():
        parts = cells(line) if line.startswith('|') else []
        if parts and re.fullmatch(r'T-\d+', parts[0]):
            if len(parts) < 6:
                problems.append('task %s has fewer than six board columns' % parts[0])
                continue
            rows.append(dict(id=parts[0], title=parts[1], brief=parts[2].strip('`').strip(), deps=re.findall(r'T-\d+', parts[3]),
                             status=parts[4], verification=parts[5]))
    return states, rows


def covers(req, traces):
    number = int(req[1:])
    if re.search(r'\b%s\b' % re.escape(req), traces):
        return True
    return any(int(a) <= number <= int(b) for a, b in re.findall(r'R(\d+)\s*[–-]\s*R?(\d+)', traces))


def parse_requirements(plan):
    found = {}
    for line in plan.splitlines():
        match = re.match(r'^\|\s*`(R\d+)`\s*\|', line)
        if match and match.group(1) not in found:
            parts = cells(line)
            found[match.group(1)] = (parts[1] if len(parts) > 1 else '', parts[2] if len(parts) > 2 else '')
    return found


def parse_decisions(text):
    found = []
    for match in re.finditer(r'^## (D-\d+) · (.+)$', text, re.M):
        parts = match.group(2).split(' · ')
        if len(parts) >= 3:
            found.append(dict(id=match.group(1), title=' · '.join(parts[:-2]), state=parts[-2], date=parts[-1]))
        else:
            found.append(dict(id=match.group(1), title=match.group(2), state='', date=''))
    return found


def newest_snapshot(history):
    marks = [m.end() for m in re.finditer(r'^### State snapshot[^\n]*\n', history, re.M)]
    if not marks:
        return ''
    tail = history[marks[-1]:]
    stop = re.search(r'^#{1,6} ', tail, re.M)
    return (tail[:stop.start()] if stop else tail).strip()


def open_runs(usage):
    starts, ended = {}, set()
    columns = None
    for line in usage.splitlines():
        if not line.startswith('|'):
            continue
        parts = cells(line)
        if parts and parts[0] == 'Run ID':
            columns = {name: i for i, name in enumerate(parts)}
            continue
        needed = ('Run ID', 'Event', 'Task', 'Role')
        if columns is None or not all(k in columns for k in needed) or len(parts) <= max(columns[k] for k in needed):
            continue
        run, event = parts[columns['Run ID']], parts[columns['Event']]
        if event == 'start':
            starts.setdefault(run, dict(scope=parts[columns['Task']], role=parts[columns['Role']]))
        elif event in ('finish', 'observe-incomplete'):
            ended.add(run)
    return [run for key, run in starts.items() if key not in ended]


def layers_of(ids, deps):
    layer, order, left = {}, [], set(ids)
    while left:
        ready = sorted(t for t in left if all(d in layer for d in deps[t]))
        if not ready:
            return None
        for t in ready:
            layer[t] = 1 + max([layer[d] for d in deps[t]] or [-1])
            left.discard(t)
    return layer


def graph_svg(tasks, layer, live, ui):
    width, height, gap_x, gap_y = 170, 46, 70, 18
    by_layer = {}
    for t in tasks:
        by_layer.setdefault(layer[t['id']], []).append(t['id'])
    pos = {}
    for column, members in by_layer.items():
        for row, tid in enumerate(sorted(members)):
            pos[tid] = (10 + column * (width + gap_x), 10 + row * (height + gap_y))
    total_w = 20 + (max(by_layer) + 1) * (width + gap_x) - gap_x
    total_h = 20 + max(len(m) for m in by_layer.values()) * (height + gap_y) - gap_y
    out = ['<svg viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">' % (total_w, total_h, total_w, total_h, esc(ui['graph']))]
    for t in tasks:
        for dep in sorted(t['deps']):
            x1, y1 = pos[dep][0] + width, pos[dep][1] + height // 2
            x2, y2 = pos[t['id']][0], pos[t['id']][1] + height // 2
            mid = (x1 + x2) // 2
            out.append('<path class="edge" data-from="%s" data-to="%s" d="M%d %d C%d %d %d %d %d %d"/>' % (
                dep, t['id'], x1, y1, mid, y1, mid, y2, x2, y2))
    for t in tasks:
        x, y = pos[t['id']]
        short = t['title'] if len(t['title']) <= 26 else t['title'][:25] + '…'
        out.append('<g class="node" data-task="%s" tabindex="0" role="button"%s><rect x="%d" y="%d" width="%d" height="%d" rx="8"/>'
                   '<text class="id" x="%d" y="%d">%s</text><text x="%d" y="%d">%s</text></g>' % (
                       t['id'], ' data-live="true"' if t['id'] in live else '', x, y, width, height, x + 10, y + 17, t['id'],
                       x + 10, y + 35, esc(short)))
    out.append('</svg>')
    return ''.join(out)


def main():
    parser = argparse.ArgumentParser(description='Write the plan view of a workspace.')
    parser.add_argument('--template', required=True)
    parser.add_argument('workspace')
    parser.add_argument('output')
    args = parser.parse_args()
    ws = Path(args.workspace)
    try:
        template_text = Path(args.template).read_text(encoding='utf-8')
    except OSError as problem:
        print('cannot read the template: %s' % problem, file=sys.stderr)
        return 2
    blocks = re.findall(r'```html\n(.*?)\n```', template_text, re.S)
    if len(blocks) != 1 or not ws.is_dir():
        print('usage: the template needs one html block and the workspace must be a directory', file=sys.stderr)
        return 2
    template = blocks[0]
    problems = []
    plan = read(ws, 'plan.md')
    if not plan:
        problems.append('plan.md is missing or empty')
    focused = bool(re.search(r'^Gate:\s*Lite\b', plan, re.M))
    lang = language(plan)
    ui = UI[lang]
    reqs = parse_requirements(plan)
    tasks, states = [], DEFAULT_STATES
    if not focused:
        board = read(ws, 'task-board.md')
        if not board:
            problems.append('task-board.md is missing or empty')
        states, tasks = parse_board(board, problems)
        if board and not tasks:
            problems.append('the board has no task rows')
        seen = set()
        for t in tasks:
            if t['id'] in seen:
                problems.append('duplicate task id %s' % t['id'])
            seen.add(t['id'])
        for t in tasks:
            for dep in t['deps']:
                if dep not in seen:
                    problems.append('task %s depends on unknown task %s' % (t['id'], dep))
            if t['status'] not in states:
                problems.append('task %s has status %s, outside the board states' % (t['id'], t['status']))
            traces = ''
            if not t['brief']:
                problems.append('task %s names no brief' % t['id'])
            else:
                path = ws / t['brief']
                inside = True
                try:
                    path.resolve().relative_to(ws.resolve())
                except ValueError:
                    inside = False
                if not inside or not path.is_file():
                    problems.append('missing brief %s for task %s' % (t['brief'], t['id']))
                else:
                    found = re.search(r'^- \*\*Traces to\*\*: (.+)$', path.read_text(encoding='utf-8'), re.M)
                    traces = found.group(1) if found else ''
            t['traces'] = traces
    layer = None
    if tasks and not problems:
        layer = layers_of([t['id'] for t in tasks], {t['id']: [d for d in t['deps']] for t in tasks})
        if layer is None:
            problems.append('the dependencies form a cycle')
    if problems:
        for line in problems:
            print('refused: %s' % line)
        return 1
    tasks.sort(key=lambda t: int(t['id'][2:]))
    for t in tasks:
        t['deps'] = sorted(set(t['deps']))
    ids = [t['id'] for t in tasks]
    down = {i: sorted(t['id'] for t in tasks if i in t['deps']) for i in ids}
    cover = {r: [t['id'] for t in tasks if covers(r, t['traces'])] for r in sorted(reqs, key=lambda r: int(r[1:]))}
    decisions = parse_decisions(read(ws, 'decisions.md'))
    snapshot = newest_snapshot(read(ws, 'history.md'))
    working = open_runs(read(ws, 'resource-usage.md'))
    live = {w['scope'] for w in working}
    version = re.search(r'Methodology:\s*Tackle\s+(\d+\.\d+\.\d+)', read(ws, 'AGENTS.md'))
    now = datetime.datetime.now().astimezone()
    stamp = now.strftime('%Y-%m-%d %H:%M ') + (now.tzname() or now.strftime('%z'))
    title_line = plan.split('\n', 1)[0].lstrip('# ').strip()
    title = title_line.split('—', 1)[-1].strip() if '—' in title_line else title_line

    def scope_label(scope):
        return ui['plan_scope'] if scope == 'PLAN' else ui['run_scope'] if scope == 'RUN' else scope

    if working:
        items = ''.join('<li data-working-scope="%s">%s · %s</li>' % (esc(w['scope']), esc(scope_label(w['scope'])), esc(ui['roles'].get(w['role'], w['role'])))
                        for w in working)
        working_html = '<section id="working-now"><h2>%s</h2><ul>%s</ul></section>' % (esc(ui['working']), items)
    else:
        working_html = '<section id="working-now"><h2>%s</h2><p data-working="none">%s</p></section>' % (esc(ui['working']), esc(ui['working_none']))

    done = sum(1 for t in tasks if t['status'] == 'Complete')
    covered = sum(1 for r in cover if cover[r])
    if focused:
        summary = ui['summary_focused'].format(reqs=len(reqs))
        stats = ['%d %s' % (len(reqs), ui['s_reqs']), '%d %s' % (len(decisions), ui['s_decisions'])]
        graph_html = '<section id="graph"><h2>%s</h2><p>%s</p></section>' % (esc(ui['graph']), esc(ui['graph_none']))
        tasks_html = ''
    else:
        summary = ui['summary'].format(done=done, total=len(tasks), covered=covered, reqs=len(reqs))
        stats = ['%d %s' % (len(tasks), ui['s_tasks']), '%d %s' % (done, ui['s_done']), '%d %s' % (len(reqs), ui['s_reqs']),
                 '%d %s' % (len(decisions), ui['s_decisions'])]
        graph_html = ('<section id="graph"><h2>%s</h2><p>%s</p><div class="graph">%s</div><div class="bar"><button type="button" id="clear-trace">%s</button></div></section>'
                      % (esc(ui['graph']), esc(ui['graph_note']), graph_svg(tasks, layer, live, ui), esc(ui['clear'])))
        present = [s for s in states if any(t['status'] == s for t in tasks)]
        bar = '<button type="button" data-filter="all" aria-pressed="true">%s (%d)</button>' % (esc(ui['all']), len(tasks))
        bar += ''.join('<button type="button" data-filter="%s" aria-pressed="false">%s (%d)</button>' % (
            esc(s), esc(s), sum(1 for t in tasks if t['status'] == s)) for s in present)
        cards = []
        for t in tasks:
            traced = [r for r in cover if t['id'] in cover[r]]
            cards.append(
                '<article class="task" id="task-%s" data-status="%s" data-upstream="%s" data-downstream="%s"%s>'
                '<h3>%s</h3><p><span class="mono muted">%s</span> <span class="badge">%s</span>%s</p>'
                '<div class="detail"><p>%s: %s</p><p>%s: %s</p><p>%s: %s</p><p>%s: <code>%s</code></p>'
                '<p><button type="button" data-trace="up">%s</button> <button type="button" data-trace="down">%s</button></p></div></article>' % (
                    t['id'], esc(t['status']), ' '.join(sorted(t['deps'])), ' '.join(sorted(down[t['id']])),
                    ' data-live="true"' if t['id'] in live else '', esc(t['title']), t['id'], esc(t['status']),
                    ' <span class="live">%s</span>' % esc(ui['live']) if t['id'] in live else '',
                    esc(ui['needs']), esc(', '.join(sorted(t['deps'])) or ui['nothing']),
                    esc(ui['unblocks']), esc(', '.join(sorted(down[t['id']])) or ui['nothing']),
                    esc(ui['requirements']), esc(', '.join(traced) or ui['nothing']), esc(ui['brief']), esc(t['brief']),
                    esc(ui['trace_up']), esc(ui['trace_down'])))
        tasks_html = '<section id="tasks"><h2>%s</h2><div class="bar">%s</div><div class="tasks">%s</div></section>' % (
            esc(ui['tasks']), bar, ''.join(cards))
    rows = []
    for r in cover:
        links = ', '.join('<a href="#task-%s">%s</a>' % (t, t) for t in cover[r])
        rows.append('<tr><td class="mono">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            esc(r), esc(reqs[r][0]), esc(reqs[r][1]), links if links else '<span class="muted">%s</span>' % esc(ui['no_task'])))
    coverage_html = '<section id="coverage"><h2>%s</h2><table><tr><th>%s</th><th></th><th>%s</th><th>%s</th></tr>%s</table></section>' % (
        esc(ui['coverage']), esc(ui['req']), esc(ui['check']), esc(ui['covered_by']), ''.join(rows))
    snapshot_html = '<section id="snapshot"><h2>%s</h2><pre>%s</pre></section>' % (
        esc(ui['snapshot']), esc(snapshot) if snapshot else esc(ui['snapshot_none']))
    technical = ''
    if tasks:
        technical += '<table><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>%s</table>' % (
            esc(ui['task']), esc(ui['status']), esc(ui['brief']), esc(ui['verification']), ''.join(
                '<tr><td class="mono">%s</td><td>%s</td><td><code>%s</code></td><td>%s</td></tr>' % (
                    t['id'], esc(t['status']), esc(t['brief']), esc(t['verification'])) for t in tasks))
    technical += '<h3>%s</h3><table><tr><th>%s</th><th></th><th>%s</th><th>%s</th></tr>%s</table>' % (
        esc(ui['decisions']), esc(ui['decision']), esc(ui['state']), esc(ui['date']), ''.join(
            '<tr><td class="mono">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (d['id'], esc(d['title']), esc(d['state']), esc(d['date']))
            for d in decisions))
    footer = '<p>%s%s · <a href="%s" target="_blank" rel="noopener noreferrer">%s</a></p><p>%s %s</p>' % (
        esc(ui['made_with']), ' ' + version.group(1) if version else '', REPO_URL, REPO_URL.split('//', 1)[1], esc(ui['built']), esc(stamp))
    island = json.dumps(dict(
        schema='tackle-plan-view/1', focused=focused, language=lang, built=stamp,
        tasks=[dict(id=t['id'], status=t['status'], deps=t['deps'], title=t['title'], brief=t['brief'], traces=t['traces']) for t in tasks],
        requirements={r: cover[r] for r in cover}, decisions=[d['id'] for d in decisions], snapshot=snapshot, working=working),
        ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    values = dict(lang=lang, title=esc(title), summary=esc(summary), stats=''.join('<span>%s</span>' % esc(s) for s in stats),
                  working=working_html, graph=graph_html, tasks=tasks_html, coverage=coverage_html, snapshot=snapshot_html,
                  technical=technical, footer=footer, island=island, ui_technical=esc(ui['technical']),
                  ui_technical_note=esc(ui['technical_note']))
    missing = sorted(set(re.findall(r'\{\{(\w+)\}\}', template)) - set(values))
    if missing:
        print('the template names unknown slots: %s' % ', '.join(missing), file=sys.stderr)
        return 2
    page = re.sub(r'\{\{(\w+)\}\}', lambda m: values[m.group(1)], template)
    try:
        Path(args.output).write_text(page + '\n', encoding='utf-8')
    except OSError as problem:
        print('cannot write the output: %s' % problem, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
```
