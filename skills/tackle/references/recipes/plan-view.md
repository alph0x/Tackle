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
STATE_CLASS = {'Complete': 'done', 'In progress': 'prog', 'Checking': 'prog', 'Ready to run': 'ready',
               'Blocked': 'block', 'Interrupted': 'block', 'Unverifiable': 'block', 'Waiting on owner': 'wait'}
UI = {
    'en': dict(
        skip='Skip to content', theme='Switch between light and dark', progress='Progress', kicker='Plan',
        n_graph='Task graph', n_tasks='Tasks', n_now='Where we are', n_tech='Details',
        working='Working now', working_none='No session works on this plan right now.', plan_scope='The plan',
        run_scope='The run', live='Live', graph='How the work connects',
        graph_note='Each arrow points from a task to the work that needs it. Select a task to trace it.',
        graph_reduced='An arrow that a longer path already implies is left out. Each task lists everything it needs.',
        graph_none='This plan has no task board, so the view shows no graph.', clear='Clear the trace',
        stage='Stage {n}', stage_count='{done} of {total} complete', stage_note='A stage is a column of the graph, not an order of work.',
        states={},
        tasks='Tasks', all='All', needs='Needs', unblocks='Unblocks', nothing='nothing', requirements='Requirements',
        brief='Brief', trace_up='Trace what it needs', trace_down='Trace what it unblocks',
        coverage='Requirement coverage', req='Requirement', check='What you can observe', check_lite='How it is checked',
        covered_by='Tasks', no_task='No task yet', validation='Validation', snapshot='Where we are',
        snapshot_none='No snapshot is recorded.', technical='Technical details',
        technical_note='Requirements, ids, raw statuses and the decision log.', task='Task',
        status='Status', verification='Verification', decisions='Decision log', decision='Decision', state='State',
        date='Date', made_with='Made with Tackle', built='Built',
        st_done='Tasks complete', st_cov='Requirements with a task', st_dec='Decisions', st_open='Sessions at work',
        st_reqs='Requirements', st_checks='Checks',
        complete='complete', bar_caption='{done} of {total} tasks are complete.',
        summary_focused='This plan has no task board. It lists {reqs} requirements.',
        roles={'executor': 'Doing the work', 'adversary': 'Independent review', 'adversary reviewer': 'Independent review',
               'semantic reviewer': 'Independent review', 'readiness reviewer': 'Checking the plan is ready',
               'brief compiler': 'Preparing the task briefs', 'auditor': 'Independent audit', 'variant reader': 'Reviewing test traps',
               'trap author': 'Writing test traps', 'diagnosis reader': 'Reading the results', 'coordinator': 'Coordinating the work',
               'designer': 'Designing the page'}),
    'es': dict(
        skip='Ir al contenido', theme='Cambiar entre claro y oscuro', progress='Avance', kicker='Plan',
        n_graph='Grafo de tareas', n_tasks='Tareas', n_now='Dónde estamos', n_tech='Detalle',
        working='En marcha ahora', working_none='Ninguna sesión trabaja en este plan ahora.', plan_scope='El plan',
        run_scope='La ejecución', live='En curso', graph='Cómo se conecta el trabajo',
        graph_note='Cada flecha va de una tarea al trabajo que la necesita. Elige una tarea para seguir su traza.',
        graph_reduced='Se omite la flecha que un camino más largo ya implica. Cada tarea lista todo lo que necesita.',
        graph_none='Este plan no tiene tablero de tareas, así que la vista no muestra grafo.', clear='Quitar la traza',
        stage='Etapa {n}', stage_count='{done} de {total} completas', stage_note='Una etapa es una columna del grafo, no un orden de trabajo.',
        states={'Draft': 'Borrador', 'Ready to run': 'Lista para ejecutar', 'In progress': 'En curso', 'Checking': 'En verificación',
                'Complete': 'Completa', 'Blocked': 'Bloqueada', 'Interrupted': 'Interrumpida', 'Skipped': 'Omitida',
                'Unverifiable': 'No verificable', 'Waiting on owner': 'Esperando al responsable'},
        tasks='Tareas', all='Todas', needs='Necesita', unblocks='Habilita', nothing='nada', requirements='Requisitos',
        brief='Brief', trace_up='Seguir lo que necesita', trace_down='Seguir lo que habilita',
        coverage='Cobertura de requisitos', req='Requisito', check='Qué se puede observar', check_lite='Cómo se comprueba',
        covered_by='Tareas', no_task='Sin tarea todavía', validation='Validación', snapshot='Dónde estamos',
        snapshot_none='No hay instantánea registrada.', technical='Detalle técnico',
        technical_note='Requisitos, ids, estados crudos y el registro de decisiones.', task='Tarea',
        status='Estado', verification='Verificación', decisions='Registro de decisiones', decision='Decisión', state='Estado',
        date='Fecha', made_with='Hecho con Tackle', built='Generado',
        st_done='Tareas completas', st_cov='Requisitos con tarea', st_dec='Decisiones', st_open='Sesiones en marcha',
        st_reqs='Requisitos', st_checks='Comprobaciones',
        complete='completo', bar_caption='{done} de {total} tareas están completas.',
        summary_focused='Este plan no tiene tablero de tareas. Lista {reqs} requisitos.',
        roles={'executor': 'Haciendo el trabajo', 'adversary': 'Revisión independiente', 'adversary reviewer': 'Revisión independiente',
               'semantic reviewer': 'Revisión independiente', 'readiness reviewer': 'Revisando que el plan esté listo',
               'brief compiler': 'Preparando los briefs', 'auditor': 'Auditoría independiente', 'variant reader': 'Revisando trampas de prueba',
               'trap author': 'Escribiendo trampas de prueba', 'diagnosis reader': 'Leyendo los resultados',
               'coordinator': 'Coordinando el trabajo', 'designer': 'Diseñando la página'}),
}
STOP = {
    'en': 'the and of to is are in for with that on each it as by be this from or an at which not have has will its their'.split(),
    'es': 'el los las del una unos unas para con por que como cada sus se lo es al y en de la un no más pero también'.split(),
    'fr': 'le les des du une est et pour que qui dans pas sur avec chaque sont ce cette au aux ou mais plus la de en un'.split(),
    'pt': 'os as dos das uma um para com por que como cada seu sua são não mas também mais está do da no na em de o a e'.split(),
    'de': 'der die das und ist sind nicht ein eine einen mit für auf von zu den dem des jede jeder wird werden nach bei auch'.split(),
}
CHARS = {'es': 'ñ¿¡', 'pt': 'ãõ', 'fr': 'èêàùâîôûœ', 'de': 'ßä'}


def esc(value):
    return html.escape(str(value), quote=True)


def read(ws, name):
    path = ws / name
    return path.read_text(encoding='utf-8') if path.is_file() else ''


def language(plan):
    """English unless Spanish shows positive, clearly leading evidence."""
    words = re.findall(r'[^\W\d_]+', plan.lower())
    homes = {}
    for code, listed in STOP.items():
        for word in listed:
            homes.setdefault(word, set()).add(code)
    score = {code: 0.0 for code in STOP}
    for word in words:
        for code in homes.get(word, ()):
            score[code] += 1.0 / len(homes[word])
    for code, chars in CHARS.items():
        score[code] += 2 * sum(plan.lower().count(c) for c in chars)
    ranked = sorted(score, key=lambda c: -score[c])
    best, second = ranked[0], ranked[1]
    return 'es' if best == 'es' and score['es'] >= 2 and score['es'] > score[second] else 'en'


def cells(line):
    body = line.strip()
    if body.startswith('|'):
        body = body[1:]
    if body.endswith('|') and not body.endswith('\\|'):
        body = body[:-1]
    return [c.strip().replace('\\|', '|') for c in re.split(r'(?<!\\)\|', body)]


def brief_path(cell):
    link = re.search(r'\]\(([^)]*)\)', cell)
    return (link.group(1) if link else cell).strip('`').strip()


def parse_board(text, problems):
    flat = ' '.join(text.split())
    found = re.search(r'States:\s*([^.]*)\.', flat)
    states = [s.strip() for s in found.group(1).split(',') if s.strip()] if found else list(DEFAULT_STATES)
    rows, columns = [], None
    for line in text.splitlines():
        if not line.startswith('|'):
            columns = None
            continue
        parts = cells(line)
        names = [p.lower() for p in parts]
        if names and names[0] == 'task' and 'status' in names:
            columns = {n: i for i, n in enumerate(names)}
            continue
        if columns is None or not re.fullmatch(r'T-\d+', parts[0]):
            continue
        pick = lambda name, default: columns.get(name, default)
        need = max(pick('what', 1), pick('brief', 2), pick('depends on', 3), pick('status', 4), pick('verification', 5))
        if len(parts) <= need:
            problems.append('task %s has fewer cells than the task table header' % parts[0])
            continue
        rows.append(dict(id=parts[0], title=parts[pick('what', 1)], brief=brief_path(parts[pick('brief', 2)]),
                         deps=re.findall(r'T-\d+', parts[pick('depends on', 3)]), status=parts[pick('status', 4)],
                         verification=parts[pick('verification', 5)]))
    return states, rows


def covers(req, traces):
    number = int(req[1:])
    if re.search(r'\b%s\b' % re.escape(req), traces):
        return True
    return any(int(a) <= number <= int(b) for a, b in re.findall(r'R(\d+)\s*[–-]\s*R?(\d+)', traces))


def by_id(text):
    marks = [(m.start(), m.end(), m.group(0)) for m in re.finditer(r'\bR\d+\b', text)]
    found = {}
    for k, (_, end, rid) in enumerate(marks):
        stop = marks[k + 1][0] if k + 1 < len(marks) else len(text)
        found.setdefault(rid, text[end:stop].replace('`', '').strip(' \t;,.:—–-→'))
    return found


def lite_fields(text):
    fields = {}
    for m in re.finditer(r'^- ([^:\n]+): (.*(?:\n[ \t]+\S.*)*)', text, re.M):
        fields.setdefault(m.group(1).strip().lower(), ' '.join(m.group(2).split()))
    return fields


def parse_requirements(plan):
    found = {}
    for line in plan.splitlines():
        match = re.match(r'^\|\s*`(R\d+)`\s*\|', line)
        if match and match.group(1) not in found:
            parts = cells(line)
            found[match.group(1)] = (parts[1] if len(parts) > 1 else '', parts[2] if len(parts) > 2 else '')
    fields = lite_fields(plan)
    purpose = next((v for k, v in fields.items() if k.startswith('purpose')), '')
    checks = by_id(fields.get('cases → checks', fields.get('cases -> checks', '')))
    for rid, text in by_id(purpose).items():
        found.setdefault(rid, (text, checks.get(rid, '')))
    return found, fields


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


def objective_of(plan):
    match = re.search(r'^## (?:\d+\.\s*)?(?:Objective|Objetivo)[^\n]*\n+(.*?)(?=^#{1,6} |\Z)', plan, re.M | re.S)
    if not match:
        return ''
    paragraph = ' '.join(match.group(1).strip().split('\n\n')[0].split())
    paragraph = re.sub(r'[`*]', '', paragraph)
    return paragraph if len(paragraph) <= 420 else paragraph[:420].rsplit(' ', 1)[0] + '…'


def open_runs(usage):
    starts, ended, columns = {}, set(), None
    needed = ('Run ID', 'Event', 'Task', 'Role')
    for line in usage.splitlines():
        if not line.startswith('|'):
            continue
        parts = cells(line)
        if parts and parts[0] == 'Run ID':
            columns = {name: i for i, name in enumerate(parts)}
            continue
        if columns is None or not all(k in columns for k in needed) or len(parts) <= max(columns[k] for k in needed):
            continue
        run, event = parts[columns['Run ID']], parts[columns['Event']]
        if event == 'start':
            starts.setdefault(run, dict(scope=parts[columns['Task']], role=parts[columns['Role']]))
        elif event in ('finish', 'observe-incomplete'):
            ended.add(run)
    return [run for key, run in starts.items() if key not in ended]


def stages_of(ids, deps):
    stage, left = {}, set(ids)
    while left:
        ready = sorted(t for t in left if all(d in stage for d in deps[t]))
        if not ready:
            return None
        for t in ready:
            stage[t] = 1 + max([stage[d] for d in deps[t]] or [-1])
            left.discard(t)
    return stage


def reduce_edges(ids, deps):
    above = {}

    def ancestors(i):
        if i not in above:
            found = set()
            for d in deps[i]:
                found |= {d} | ancestors(d)
            above[i] = found
        return above[i]

    return [(d, i) for i in ids for d in sorted(deps[i]) if not any(d in ancestors(o) for o in deps[i] if o != d)]


WORK_LIMIT = 600000


def crossings(order, by_column, spent=None):
    total = 0
    for column in range(len(order) - 1):
        pos = {n: k for k, n in enumerate(order[column + 1])}
        left = {n: k for k, n in enumerate(order[column])}
        pairs = [(left[a], pos[b]) for a, b in by_column[column]]
        if spent is not None:
            spent[0] += len(pairs) * len(pairs) // 2 + len(pairs)
        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                if (pairs[i][0] - pairs[j][0]) * (pairs[i][1] - pairs[j][1]) < 0:
                    total += 1
    return total


def layered(ids, stage, edges):
    """Split long edges with waypoints so every link joins adjacent stages, then order each stage to cut crossings."""
    last = max(stage.values())
    order = [[] for _ in range(last + 1)]
    for i in ids:
        order[stage[i]].append(i)
    links, chains = [], {}
    for a, b in edges:
        chain = [a] + ['%s>%s@%d' % (a, b, s) for s in range(stage[a] + 1, stage[b])] + [b]
        chains[(a, b)] = chain
        for s in range(stage[a] + 1, stage[b]):
            order[s].append(chain[s - stage[a]])
        links += list(zip(chain, chain[1:]))
    column_of = {n: c for c, col in enumerate(order) for n in col}
    by_column = [[] for _ in order]
    for a, b in links:
        by_column[column_of[a]].append((a, b))
    up, down = {}, {}
    for a, b in links:
        down.setdefault(a, []).append(b)
        up.setdefault(b, []).append(a)
    spent = [0]

    def improve(start):
        order = [list(c) for c in start]
        best, best_score = [list(c) for c in order], crossings(order, by_column, spent)
        for sweep in range(24):
            if spent[0] > WORK_LIMIT:
                break
            columns = range(1, len(order)) if sweep % 2 == 0 else range(len(order) - 2, -1, -1)
            for c in columns:
                ref = order[c - 1 if sweep % 2 == 0 else c + 1]
                where = {n: k for k, n in enumerate(ref)}
                near = up if sweep % 2 == 0 else down
                keep = {n: k for k, n in enumerate(order[c])}
                order[c].sort(key=lambda n: (sum(where[m] for m in near.get(n, []) if m in where) / len(near[n])
                                            if any(m in where for m in near.get(n, [])) else keep[n], keep[n]))
            score = crossings(order, by_column, spent)
            if score < best_score:
                best, best_score = [list(c) for c in order], score
        order, better = best, True
        while better and best_score and spent[0] <= WORK_LIMIT:
            better = False
            for c in range(len(order)):
                for k in range(len(order[c]) - 1):
                    if spent[0] > WORK_LIMIT:
                        break
                    order[c][k], order[c][k + 1] = order[c][k + 1], order[c][k]
                    score = crossings(order, by_column, spent)
                    if score < best_score:
                        best_score, better = score, True
                    else:
                        order[c][k], order[c][k + 1] = order[c][k + 1], order[c][k]
        return order, best_score

    results = [improve(order), improve([list(reversed(c)) for c in order])]
    best, score = min(results, key=lambda r: r[1])
    return best, chains, score


def wrap(text, width=27, lines=2):
    words, out, line = text.split(), [], ''
    for word in words:
        while len(word) > width:
            if line:
                out.append(line)
                line = ''
            out.append(word[:width])
            word = word[width:]
        if len(line) + len(word) + (1 if line else 0) <= width:
            line = (line + ' ' + word).strip()
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][:width - 1].rstrip() + '…'
    return out or ['']


def graph_svg(tasks, stage, edges, live, ui):
    ids = [t['id'] for t in tasks]
    title = {t['id']: t['title'] for t in tasks}
    state = {t['id']: t['status'] for t in tasks}
    kids = {i: [b for a, b in edges if a == i] for i in ids}
    late = {}

    def latest(i):
        if i not in late:
            late[i] = min(latest(k) for k in kids[i]) - 1 if kids[i] else (max(stage.values()) if stage[i] else 0)
        return late[i]

    options = [(stage, layered(ids, stage, edges)), ({i: latest(i) for i in ids}, None)]
    options[1] = (options[1][0], layered(ids, options[1][0], edges))
    stage, (order, chains, _) = min(options, key=lambda o: o[1][2])
    node_w, node_h, dummy_h, gap_y, pad, gap_x, head = 208, 70, 26, 16, 16, 64, 58
    band_w = node_w + 2 * pad
    heights = [sum(node_h if n in title else dummy_h for n in col) + gap_y * (len(col) - 1) for col in order]
    top = max(heights)
    total_w = len(order) * band_w + (len(order) - 1) * gap_x + 2 * 6
    total_h = head + top + 2 * pad
    where = {}
    for c, col in enumerate(order):
        x = 6 + c * (band_w + gap_x)
        y = head + pad + (top - heights[c]) / 2
        for n in col:
            size = node_h if n in title else dummy_h
            where[n] = (x, y, size)
            y += size + gap_y
    out = ['<svg viewBox="0 0 %d %d" width="%d" height="%d" role="group" aria-label="%s"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
           '<path class="arrowhead" d="M 0 1 L 10 5 L 0 9 z"/></marker></defs>' % (total_w, total_h, total_w, total_h, esc(ui['graph']))]
    for c, col in enumerate(order):
        x = 6 + c * (band_w + gap_x)
        done = sum(1 for n in col if n in title and state[n] == 'Complete')
        count = sum(1 for n in col if n in title)
        out.append('<rect class="band" x="%d" y="0" width="%d" height="%d" rx="16"/><text class="band-h" x="%d" y="24">%s</text>'
                   '<text class="band-c" x="%d" y="42">%s</text>' % (
                       x, band_w, total_h, x + pad, esc(ui['stage'].format(n=c + 1)), x + pad,
                       esc(ui['stage_count'].format(done=done, total=count))))
    for (a, b), chain in chains.items():
        points = []
        for k, n in enumerate(chain):
            x, y, size = where[n]
            mid = y + size / 2
            if k == 0:
                points.append((x + pad + node_w, mid))
            elif k == len(chain) - 1:
                points.append((x + pad, mid))
            else:
                points += [(x, mid), (x + band_w, mid)]
        path = 'M%.1f %.1f' % points[0]
        for p, q in zip(points, points[1:]):
            if abs(p[1] - q[1]) < 0.5 and q[0] - p[0] <= band_w:
                path += ' L%.1f %.1f' % q
            else:
                half = (q[0] - p[0]) / 2
                path += ' C%.1f %.1f %.1f %.1f %.1f %.1f' % (p[0] + half, p[1], q[0] - half, q[1], q[0], q[1])
        out.append('<path class="edge" data-from="%s" data-to="%s" d="%s" marker-end="url(#arrow)"/>' % (a, b, path))
    for t in tasks:
        x, y, _ = where[t['id']]
        x += pad
        lines = wrap(t['title'])
        text = ''.join('<tspan x="%d" dy="%d">%s</tspan>' % (x + 12, 0 if k == 0 else 16, esc(line)) for k, line in enumerate(lines))
        out.append('<g class="node s-%s" data-task="%s" data-status="%s"%s tabindex="0" role="button" aria-label="%s"><title>%s</title>'
                   '<rect x="%d" y="%.1f" width="%d" height="%d" rx="12"/><circle cx="%d" cy="%.1f" r="4" class="dot-%s"/>'
                   '<text class="nid" x="%d" y="%.1f">%s</text><text class="nt" x="%d" y="%.1f">%s</text></g>' % (
                       STATE_CLASS.get(t['status'], 'draft'), t['id'], esc(t['status']), ' data-live="true"' if t['id'] in live else '',
                       esc('%s · %s' % (t['id'], t['title'])), esc('%s · %s · %s' % (t['id'], t['title'], ui['states'].get(t['status'], t['status']))),
                       x, y, node_w, node_h, x + 16, y + 17, STATE_CLASS.get(t['status'], 'draft'),
                       x + 26, y + 21, t['id'], x + 12, y + 41, text))
    out.append('</svg>')
    return ''.join(out)


def fill(template, values):
    missing = sorted(set(re.findall(r'\{\{(\w+)\}\}', template)) - set(values))
    if missing:
        raise KeyError(', '.join(missing))
    return re.sub(r'\{\{(\w+)\}\}', lambda m: values[m.group(1)], template)


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
    reqs, fields = parse_requirements(plan)
    if focused and not reqs:
        problems.append('the Focused plan names no requirement id in its Purpose / requirements line or its criteria table')
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
                try:
                    path.resolve().relative_to(ws.resolve())
                except ValueError:
                    problems.append('brief %s for task %s is outside the workspace' % (t['brief'], t['id']))
                else:
                    if not path.is_file():
                        problems.append('missing brief %s for task %s' % (t['brief'], t['id']))
                    else:
                        found = re.search(r'^- \*\*Traces to\*\*: (.+)$', path.read_text(encoding='utf-8'), re.M)
                        traces = found.group(1) if found else ''
            t['traces'] = traces
    stage = None
    if tasks and not problems:
        stage = stages_of([t['id'] for t in tasks], {t['id']: list(t['deps']) for t in tasks})
        if stage is None:
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
    snapshot = newest_snapshot(read(ws, 'history.md')) or fields.get('state', '')
    working = open_runs(read(ws, 'resource-usage.md'))
    live = {w['scope'] for w in working}
    version = re.search(r'Methodology:\s*Tackle\s+(\d+\.\d+\.\d+)', read(ws, 'AGENTS.md'))
    now = datetime.datetime.now().astimezone()
    stamp = now.strftime('%Y-%m-%d %H:%M ') + (now.tzname() or now.strftime('%z'))
    heading = re.search(r'^# (.+)$', plan, re.M)
    title_line = heading.group(1).strip() if heading else ''
    title = title_line.split('—', 1)[-1].strip() if '—' in title_line else title_line
    kicker = title_line.split('—', 1)[0].strip() if '—' in title_line else ui['kicker']

    def scope_label(scope):
        return ui['plan_scope'] if scope == 'PLAN' else ui['run_scope'] if scope == 'RUN' else scope

    if working:
        items = ''.join('<li data-working-scope="%s">%s · %s</li>' % (esc(w['scope']), esc(scope_label(w['scope'])), esc(ui['roles'].get(w['role'], w['role'])))
                        for w in working)
        working_html = '<section id="working-now" data-reveal><h2 class="eyebrow">%s</h2><ul>%s</ul></section>' % (esc(ui['working']), items)
    else:
        working_html = '<section id="working-now" data-reveal><h2 class="eyebrow">%s</h2><p data-working="none">%s</p></section>' % (
            esc(ui['working']), esc(ui['working_none']))

    done = sum(1 for t in tasks if t['status'] == 'Complete')
    covered = sum(1 for r in cover if cover[r])
    nav = []
    if focused:
        progress = '<div class="ring" style="--off:390"><svg viewBox="0 0 148 148" width="148" height="148" aria-hidden="true"><circle class="track" cx="74" cy="74" r="62"/></svg>' \
                   '<div class="num"><b>%d</b><small>%s</small></div></div><p class="cap">%s</p>' % (
                       len(reqs), esc(ui['st_reqs']), esc(ui['summary_focused'].format(reqs=len(reqs))))
        stats = [(ui['st_reqs'], len(reqs)), (ui['st_checks'], sum(1 for v in reqs.values() if v[1])), (ui['st_dec'], len(decisions)),
                 (ui['st_open'], len(working))]
        graph_html = '<section class="sec" id="graph" data-reveal><div class="sh"><h2>%s</h2><p>%s</p></div></section>' % (esc(ui['graph']), esc(ui['graph_none']))
        tasks_html = ''
    else:
        pct = round(100 * done / len(tasks))
        counts = {}
        for t in tasks:
            counts[t['status']] = counts.get(t['status'], 0) + 1
        present = [s for s in states if s in counts]
        segs = ''.join('<i class="%s" style="flex:%d" title="%s · %d"></i>' % (STATE_CLASS.get(s, 'draft'), counts[s], esc(ui['states'].get(s, s)), counts[s]) for s in present)
        legend = ''.join('<li><i class="dot %s" aria-hidden="true"></i><span>%s</span><b>%d</b></li>' % (STATE_CLASS.get(s, 'draft'), esc(ui['states'].get(s, s)), counts[s]) for s in present)
        progress = ('<div class="ring" style="--off:%.1f"><svg viewBox="0 0 148 148" width="148" height="148" aria-hidden="true"><circle class="track" cx="74" cy="74" r="62"/>'
                    '<circle class="val" cx="74" cy="74" r="62"/></svg><div class="num"><b>%d%%</b><small>%s</small></div></div><p class="cap">%s</p>'
                    '<div class="segbar">%s</div><ul class="seglegend">%s</ul>') % (
            390 * (1 - pct / 100), pct, esc(ui['complete']), esc(ui['bar_caption'].format(done=done, total=len(tasks))), segs, legend)
        stats = [(ui['st_done'], '%d / %d' % (done, len(tasks))), (ui['st_cov'], '%d / %d' % (covered, len(reqs))),
                 (ui['st_dec'], len(decisions)), (ui['st_open'], len(working))]
        edges = reduce_edges(ids, {t['id']: t['deps'] for t in tasks})
        nav += [('graph', ui['n_graph']), ('tasks', ui['n_tasks'])]
        graph_html = ('<section class="sec" id="graph" data-reveal><div class="sh"><h2>%s</h2><p>%s</p></div><div class="map">'
                      '<div class="map-bar"><span>%s</span><button type="button" class="chip" id="clear-trace">%s</button></div>'
                      '<div class="gscroll">%s</div></div></section>') % (
            esc(ui['graph']), esc(ui['graph_note'] + ' ' + ui['stage_note']), esc(ui['graph_reduced']), esc(ui['clear']),
            graph_svg(tasks, stage, edges, live, ui))
        bar = '<button type="button" class="chip" data-filter="all" aria-pressed="true">%s <b>%d</b></button>' % (esc(ui['all']), len(tasks))
        bar += ''.join('<button type="button" class="chip" data-filter="%s" aria-pressed="false"><i class="dot %s" aria-hidden="true"></i>%s <b>%d</b></button>' % (
            esc(s), STATE_CLASS.get(s, 'draft'), esc(ui['states'].get(s, s)), counts[s]) for s in present)
        cards = []
        for t in tasks:
            traced = [r for r in cover if t['id'] in cover[r]]
            cards.append(
                '<article class="task" id="task-%s" data-status="%s" data-upstream="%s" data-downstream="%s"%s>'
                '<div class="tc-top"><span class="mono">%s</span>%s<span class="pill"><i class="dot %s" aria-hidden="true"></i>%s</span></div>'
                '<h3>%s</h3>'
                '<div class="detail"><p>%s: %s</p><p>%s: %s</p><p>%s: %s</p><p>%s: <code>%s</code></p>'
                '<p><button type="button" data-trace="up">%s</button> <button type="button" data-trace="down">%s</button></p></div></article>' % (
                    t['id'], esc(t['status']), ' '.join(sorted(t['deps'])), ' '.join(sorted(down[t['id']])),
                    ' data-live="true"' if t['id'] in live else '', t['id'],
                    ' <span class="live">%s</span>' % esc(ui['live']) if t['id'] in live else '', STATE_CLASS.get(t['status'], 'draft'), esc(ui['states'].get(t['status'], t['status'])),
                    esc(t['title']), esc(ui['needs']), esc(', '.join(sorted(t['deps'])) or ui['nothing']),
                    esc(ui['unblocks']), esc(', '.join(sorted(down[t['id']])) or ui['nothing']),
                    esc(ui['requirements']), esc(', '.join(traced) or ui['nothing']), esc(ui['brief']), esc(t['brief']),
                    esc(ui['trace_up']), esc(ui['trace_down'])))
        tasks_html = '<section class="sec" id="tasks" data-reveal><div class="sh"><h2>%s</h2></div><div class="bar">%s</div><div class="tasks">%s</div></section>' % (
            esc(ui['tasks']), bar, ''.join(cards))
    nav.append(('snapshot', ui['n_now']))
    nav.append(('technical', ui['n_tech']))
    rows = []
    for r in cover:
        links = ', '.join('<a href="#task-%s">%s</a>' % (t, t) for t in cover[r])
        none = '<span>%s</span>' % esc(ui['no_task']) if not focused else ''
        rows.append('<tr><td class="mono">%s</td><td>%s</td><td>%s</td>%s</tr>' % (
            esc(r), esc(reqs[r][0]), esc(reqs[r][1]),
            '' if focused else '<td>%s</td>' % (links or none)))
    head_cells = '<th>%s</th><th></th><th>%s</th>%s' % (esc(ui['req']), esc(ui['check_lite'] if focused else ui['check']),
                                                        '' if focused else '<th>%s</th>' % esc(ui['covered_by']))
    snapshot_html = '<section class="sec" id="snapshot" data-reveal><div class="sh"><h2>%s</h2></div><p class="snap">%s</p></section>' % (
        esc(ui['snapshot']), esc(snapshot) if snapshot else esc(ui['snapshot_none']))
    technical = '<h3>%s</h3><div class="tw"><table><tr>%s</tr>%s</table></div>' % (esc(ui['coverage']), head_cells, ''.join(rows))
    if focused and fields.get('validation'):
        technical += '<p><b>%s</b>: %s</p>' % (esc(ui['validation']), esc(fields['validation']))
    if tasks:
        technical += '<h3>%s</h3><div class="tw"><table><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>%s</table></div>' % (
            esc(ui['tasks']), esc(ui['task']), esc(ui['status']), esc(ui['brief']), esc(ui['verification']), ''.join(
                '<tr><td class="mono">%s</td><td>%s</td><td><code>%s</code></td><td>%s</td></tr>' % (
                    t['id'], esc(t['status']), esc(t['brief']), esc(t['verification'])) for t in tasks))
    technical += '<h3>%s</h3><div class="tw"><table><tr><th>%s</th><th></th><th>%s</th><th>%s</th></tr>%s</table></div>' % (
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
    objective = objective_of(plan)
    values = dict(
        lang=lang, title=esc(title), brand=esc(title if len(title) <= 40 else title[:39] + '…'), kicker=esc(kicker),
        objective='<p class="objective">%s</p>' % esc(objective) if objective else '', progress=progress,
        stats=''.join('<div class="stat"><span class="k">%s</span><b>%s</b></div>' % (esc(k), esc(v)) for k, v in stats),
        nav=''.join('<a href="#%s">%s</a>' % (anchor, esc(label)) for anchor, label in nav),
        working=working_html, graph=graph_html, tasks=tasks_html, snapshot=snapshot_html, technical=technical, footer=footer,
        island=island, ui_skip=esc(ui['skip']), ui_theme=esc(ui['theme']), ui_progress=esc(ui['progress']),
        ui_technical=esc(ui['technical']), ui_technical_note=esc(ui['technical_note']))
    try:
        page = fill(template, values)
    except KeyError as missing:
        print('the template names unknown slots: %s' % missing, file=sys.stderr)
        return 2
    try:
        Path(args.output).write_text(page + '\n', encoding='utf-8')
    except OSError as problem:
        print('cannot write the output: %s' % problem, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
```
