```python
import argparse
import datetime
import hashlib
import html
import json
import os
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
        n_overview='Outcomes', n_requirements='Requirements', n_decisions='Decisions', n_export='Export',
        n_graph='Flow', n_tasks='Tasks', n_now='Status', n_tech='Details', n_arch='Architecture',
        working='Working now', working_none='No session works on this plan right now.', plan_scope='The plan',
        run_scope='The run', live='Live', graph='How the work flows',
        graph_note='Each arrow points from a task to the work that needs it. Select a task to trace it.', mission_purpose='Purpose', mission_complete='{done} of {total} recorded tasks are complete.', mission_remaining='{count} recorded tasks remain open or unfinished.', mission_achievements='Recorded achievements', mission_open_work='Open work', mission_next='Next recorded steps', mission_raw_snapshot='Raw recorded snapshot', mission_no_board='No task board is available; this view remains a focused snapshot.', stale_prose='The written status summary describes an earlier board ({as_of}); the task states have changed since, so the recorded facts below replace it until it is updated.',
        graph_reduced='An arrow that a longer path already implies is left out. Each task lists everything it needs.',
        graph_none='This plan has no task board, so the view shows no graph.', clear='Clear the trace',
        stage='Stage {n}', stage_count='{done} of {total} complete', stage_note='A stage is a column of the graph, not an order of work.',
        a_title='Before and after', a_note='How the project is put together today, and what this plan adds or changes. Select a component to see what it connects to.',
        a_views='Which view to show', a_cards='Components', a_diagram='Diagram', a_pics='Which picture to show', a_today='Today',
        a_after='After this plan', a_whole='Showing: the whole project', a_changed_only='Showing: only what changes, with its neighbors',
        a_new='New', a_change='Changed', a_stale='Source missing', a_planned='Planned', a_done='Done', a_uses='Uses', a_used='Used by',
        a_sources='Sources', a_count='Components', a_changes='Changes', a_group_count='{count} components', a_nochange='This plan changes nothing in the map.',
        a_none='No base map yet. Ask for one and this section shows the project before and after the plan.',
        a_mismatch='The map was verified at {have}, and the delta expects {want}.', a_pick='Select a component to see what it connects to.',
        states={},
        tasks='Tasks', all='All', needs='Needs', unblocks='Unblocks', nothing='nothing', requirements='Requirements',
        brief='Brief', trace_up='Trace what it needs', trace_down='Trace what it unblocks',
        coverage='Requirement coverage', req='Requirement', check='What you can observe', check_lite='How it is checked',
        covered_by='Tasks', no_task='No task yet', validation='Validation', snapshot='Where we are',
        snapshot_none='No snapshot is recorded.', technical='Technical details',
        technical_note='Open one collection to inspect its complete recorded values. Nothing is removed by the current selection or task filter.', task='Task',
        criteria_kicker='Acceptance criteria', technical_coverage_note='Each requirement, its recorded check and its task ownership.',
        technical_tasks_note='Original task states, brief paths and verification records from the board.',
        technical_decisions_note='The complete decision index. Open the decision archive above for each original body.',
        record_title='Title', technical_count='{count} records',
        a_role='Role in the project',
        a_diagram_help='Columns are the project groups. Each arrow runs from a component to the one it connects to; its words sit where it starts.',
        a_in='Incoming', a_out='Outgoing', a_detail='Connections and source files', a_types={'guide': 'Guide', 'template': 'Templates', 'document': 'Markdown documents', 'tool': 'Python tools',
                 'data': 'Records and configuration', 'mixed': 'Files and records', 'workflow': 'Automation workflow',
                 'package': 'Installable files', 'page': 'Page', 'capability': 'Capability', 'component': 'Component'},
        status='Status', verification='Verification', decisions='Decision log', decision='Decision', state='State',
        date='Date', made_with='Made with Tackle', built='Built',
        st_done='Tasks complete', st_cov='Requirements with a task', st_dec='Decisions', st_open='Sessions at work',
        st_reqs='Requirements', st_checks='Checks',
        complete='complete', bar_caption='{done} of {total} tasks are complete.', unknown='Unknown',
        outcomes='What this plan makes possible', now='Now', next='Next', owner='You',
        milestones='Milestones', source_note='Outcomes and milestones come from the plan summary. States, counts and coverage come from the board and the plan.',
        task_purpose='Purpose', requirements_intro='Each requirement keeps its exact behavior, observable output, boundary cases and valid alternatives from the plan, with the tasks that cover it.',
        behavior='Required behavior', output='Observable output/effect', boundary='Boundary cases', alternative='Valid alternatives', source_details='Exact source details',
        no_requirements='No canonical requirement rows were recorded.',
        decisions_intro='The curated story comes first. The archive keeps every decision record and its original text; a later decision can supersede an earlier one.',
        decision_story='Why the choices matter', canonical_archive='Canonical decision archive', decision_count='{count} records', search_decisions='Search decisions', clear_search='Clear search',
        search_results='Decision search results', decision_record='Decision record', raw_record='Original record',
        architecture_legend='Map legend',
        a_rel_heading='Connections in this map', a_rel_hint='Read each row as source → recorded relation → destination. Select a component to show its connections; select it again to show all.',
        a_rel_all='Recorded connections: {count}.', a_rel_focus='Connections involving {title}: {count}.',
        a_rel_list='Recorded component connections', a_rel_empty='No connections are recorded between the components shown in this map.',
        summary_focused='This plan has no task board. It lists {reqs} requirements.',
        tb_tasks='tasks complete',
        tb_strip='One cell per task, in task order',
        legend='Legend',
        legend_met='Prerequisite complete',
        legend_open='Waits on unfinished work',
        zoom='Zoom',
        zoom_in='Zoom in',
        zoom_out='Zoom out',
        fit='Fit',
        inspector_empty='Select a task to see what it needs and what it unblocks.',
        stage_list='Tasks by stage',
        tasks_lede='Every task on the board, with what it needs and what it unblocks. Filter by state or open a task for its details.',
        filter='Filter by state',
        filter_empty='No task has this state.',
        outcomes_lede='The outcomes the plan is built to deliver, in plain words.',
        search_placeholder='Search by id, word or date',
        nav='Sections',
        freshness='Snapshot generated: {built}',
        a_changes_title='What this plan changes',
        show_all='Show all {count}',
        show_less='Show fewer',
        show_diagram='Show the diagram',
        hide_diagram='Hide the diagram',
        inspector_open='Open in the task list',
        technical_title='Source records',
        a_clear='Clear the selection',
        req_toggle='Show the tasks that cover {id}',
        a_lens='Connections',
        close='Close',
        a_lens_none='None recorded.',
        a_lens_hint='Select a connected component to walk the map. Escape closes.',
        roles={'executor': 'Doing the work', 'adversary': 'Independent review', 'adversary reviewer': 'Independent review',
               'semantic reviewer': 'Independent review', 'readiness reviewer': 'Checking the plan is ready',
               'brief compiler': 'Preparing the task briefs', 'auditor': 'Independent audit', 'variant reader': 'Reviewing test traps',
               'trap author': 'Writing test traps', 'diagnosis reader': 'Reading the results', 'coordinator': 'Coordinating the work',
               'designer': 'Designing the page'}),
    'es': dict(
        skip='Ir al contenido', theme='Cambiar entre claro y oscuro', progress='Avance', kicker='Plan',
        n_overview='Resultados', n_requirements='Requisitos', n_decisions='Decisiones', n_export='Exportar',
        n_graph='Flujo', n_tasks='Tareas', n_now='Estado', n_tech='Detalle', n_arch='Arquitectura',
        working='En marcha ahora', working_none='Ninguna sesión trabaja en este plan ahora.', plan_scope='El plan',
        run_scope='La ejecución', live='En marcha', graph='Cómo fluye el trabajo',
        graph_note='Cada flecha va de una tarea al trabajo que la necesita. Elige una tarea para seguir su traza.', mission_purpose='Propósito', mission_complete='{done} de {total} tareas registradas están completas.', mission_remaining='{count} tareas registradas siguen abiertas o incompletas.', mission_achievements='Logros registrados', mission_open_work='Trabajo abierto', mission_next='Siguientes pasos registrados', mission_raw_snapshot='Instantánea registrada en bruto', mission_no_board='No hay un tablero de tareas; esta vista conserva una instantánea enfocada.', stale_prose='El resumen escrito del estado describe un tablero anterior ({as_of}); los estados de las tareas cambiaron desde entonces, así que los hechos registrados de abajo lo reemplazan hasta que se actualice.',
        graph_reduced='Se omite la flecha que un camino más largo ya implica. Cada tarea lista todo lo que necesita.',
        graph_none='Este plan no tiene tablero de tareas, así que la vista no muestra grafo.', clear='Quitar la traza',
        stage='Etapa {n}', stage_count='{done} de {total} completas', stage_note='Una etapa es una columna del grafo, no un orden de trabajo.',
        a_title='Antes y después', a_note='Cómo está armado el proyecto hoy y qué agrega o cambia este plan. Elige un componente para ver con qué se conecta.',
        a_views='Qué vista mostrar', a_cards='Componentes', a_diagram='Diagrama', a_pics='Qué imagen mostrar', a_today='Hoy',
        a_after='Después de este plan', a_whole='Se muestra: todo el proyecto', a_changed_only='Se muestra: solo lo que cambia, con sus vecinos',
        a_new='Nuevo', a_change='Cambiado', a_stale='Falta la fuente', a_planned='Planificado', a_done='Hecho', a_uses='Usa', a_used='Lo usa',
        a_sources='Fuentes', a_count='Componentes', a_changes='Cambios', a_group_count='{count} componentes', a_nochange='Este plan no cambia nada del mapa.',
        a_none='Todavía no hay un mapa base. Pídelo y esta sección muestra el proyecto antes y después del plan.',
        a_mismatch='El mapa se verificó en {have}, y el delta espera {want}.', a_pick='Elige un componente para ver con qué se conecta.',
        states={'Draft': 'Borrador', 'Ready to run': 'Lista para ejecutar', 'In progress': 'En curso', 'Checking': 'En verificación',
                'Complete': 'Completa', 'Blocked': 'Bloqueada', 'Interrupted': 'Interrumpida', 'Skipped': 'Omitida',
                'Unverifiable': 'No verificable', 'Waiting on owner': 'Esperando al responsable'},
        tasks='Tareas', all='Todas', needs='Necesita', unblocks='Habilita', nothing='nada', requirements='Requisitos',
        brief='Brief', trace_up='Seguir lo que necesita', trace_down='Seguir lo que habilita',
        coverage='Cobertura de requisitos', req='Requisito', check='Qué se puede observar', check_lite='Cómo se comprueba',
        covered_by='Tareas', no_task='Sin tarea todavía', validation='Validación', snapshot='Dónde estamos',
        snapshot_none='No hay instantánea registrada.', technical='Detalle técnico',
        technical_note='Abre una colección para consultar sus valores registrados completos. La selección y el filtro de tareas conservan todos los registros.', task='Tarea',
        criteria_kicker='Criterios de aceptación', technical_coverage_note='Cada requisito, su comprobación registrada y las tareas que lo cubren.',
        technical_tasks_note='Estados originales, rutas de briefs y verificaciones del tablero.',
        technical_decisions_note='El índice completo de decisiones. El archivo de arriba conserva cada cuerpo original.',
        record_title='Título', technical_count='{count} registros',
        a_role='Función en el proyecto',
        a_diagram_help='Las columnas son los grupos del proyecto. Cada flecha va de un componente al que conecta; sus palabras están donde empieza.',
        a_in='Entrantes', a_out='Salientes', a_detail='Conexiones y archivos fuente', a_types={'guide': 'Guía', 'template': 'Plantillas', 'document': 'Documentos Markdown', 'tool': 'Herramientas Python',
                 'data': 'Registros y configuración', 'mixed': 'Archivos y registros', 'workflow': 'Flujo automatizado',
                 'package': 'Archivos instalables', 'page': 'Página', 'capability': 'Capacidad', 'component': 'Componente'},
        status='Estado', verification='Verificación', decisions='Registro de decisiones', decision='Decisión', state='Estado',
        date='Fecha', made_with='Hecho con Tackle', built='Generado',
        st_done='Tareas completas', st_cov='Requisitos con tarea', st_dec='Decisiones', st_open='Sesiones en marcha',
        st_reqs='Requisitos', st_checks='Comprobaciones',
        complete='completo', bar_caption='{done} de {total} tareas están completas.', unknown='Desconocido',
        outcomes='Lo que este plan hace posible', now='Ahora', next='Siguiente', owner='Tú',
        milestones='Hitos', source_note='Los resultados y los hitos vienen del resumen del plan. Los estados, las cifras y la cobertura vienen del tablero y del plan.',
        task_purpose='Propósito', requirements_intro='Cada requisito conserva el comportamiento exacto, el resultado observable, los límites y las alternativas válidas del plan, con las tareas que lo cubren.',
        behavior='Comportamiento requerido', output='Resultado/efecto observable', boundary='Casos límite', alternative='Alternativas válidas', source_details='Detalles exactos de la fuente',
        no_requirements='No hay filas canónicas de requisitos registradas.',
        decisions_intro='Primero la historia curada. El archivo conserva cada decisión y su texto original; una decisión posterior puede reemplazar a una anterior.',
        decision_story='Por qué importan las decisiones', canonical_archive='Archivo canónico de decisiones', decision_count='{count} registros', search_decisions='Buscar decisiones', clear_search='Limpiar búsqueda',
        search_results='Resultados de búsqueda de decisiones', decision_record='Registro de decisión', raw_record='Registro original',
        architecture_legend='Leyenda del mapa',
        a_rel_heading='Conexiones de este mapa', a_rel_hint='Lee cada fila como origen → relación registrada → destino. Elige un componente para ver sus conexiones; elígelo otra vez para verlas todas.',
        a_rel_all='Conexiones registradas: {count}.', a_rel_focus='Conexiones que incluyen {title}: {count}.',
        a_rel_list='Conexiones registradas entre componentes', a_rel_empty='No hay conexiones registradas entre los componentes que muestra este mapa.',
        summary_focused='Este plan no tiene tablero de tareas. Lista {reqs} requisitos.',
        tb_tasks='tareas completas',
        tb_strip='Una celda por tarea, en orden',
        legend='Leyenda',
        legend_met='Requisito previo completo',
        legend_open='Espera trabajo sin terminar',
        zoom='Zoom',
        zoom_in='Acercar',
        zoom_out='Alejar',
        fit='Ajustar',
        inspector_empty='Elige una tarea para ver qué necesita y qué habilita.',
        stage_list='Tareas por etapa',
        tasks_lede='Cada tarea del tablero, con lo que necesita y lo que habilita. Filtra por estado o abre una tarea para ver su detalle.',
        filter='Filtrar por estado',
        filter_empty='Ninguna tarea tiene este estado.',
        outcomes_lede='Los resultados que el plan busca entregar, en palabras claras.',
        search_placeholder='Busca por id, palabra o fecha',
        nav='Secciones',
        freshness='Instantánea generada: {built}',
        a_changes_title='Qué cambia este plan',
        show_all='Mostrar las {count}',
        show_less='Mostrar menos',
        show_diagram='Mostrar el diagrama',
        hide_diagram='Ocultar el diagrama',
        inspector_open='Abrir en la lista de tareas',
        technical_title='Registros fuente',
        a_clear='Quitar la selección',
        req_toggle='Mostrar las tareas que cubren {id}',
        a_lens='Conexiones',
        close='Cerrar',
        a_lens_none='Ninguna registrada.',
        a_lens_hint='Elige un componente conectado para recorrer el mapa. Escape cierra.',
        roles={'executor': 'Haciendo el trabajo', 'adversary': 'Revisión independiente', 'adversary reviewer': 'Revisión independiente',
               'semantic reviewer': 'Revisión independiente', 'readiness reviewer': 'Revisando que el plan esté listo',
               'brief compiler': 'Preparando los briefs', 'auditor': 'Auditoría independiente', 'variant reader': 'Revisando trampas de prueba',
               'trap author': 'Escribiendo trampas de prueba', 'diagnosis reader': 'Leyendo los resultados',
               'coordinator': 'Coordinando el trabajo', 'designer': 'Diseñando la página'}),
}
EXPORT_UI = {
    'en': dict(export_lede='A self-contained document for readers who do not know the project: why the plan matters, where the work stands and what comes next.', plan_desc='Purpose, outcomes, scope, road map and key choices.', progress_desc='Where the work stands: what is done, what is open and the next steps.', both_desc='The plan and its progress in one document.', export_title='Share the plan', export='Export PDF', scope='Printable report', plan='Plan', progress='Progress', both='Plan and progress',
               print='Export PDF', save_pdf='In the print dialog, choose Save as PDF.', print_error='Unable to open the print dialog.',
               methodology_unavailable='Not registered (n/a)', report_planned_tasks='Planned tasks and dependencies',
               report_plan='Plan report', report_progress='Progress report', report_scope='Scope', report_built='Built',
               report_method='Methodology', report_printable='Printable report', report_tasks='Task progress',
               report_task='Task', report_what='What', report_status='Status', report_brief='Brief',
               report_dependencies='Depends on', report_verification='Verification', report_snapshot='Latest recorded state',
               report_roles='Open sessions', report_obligations='Open obligations', report_obligation='Obligation', report_owner='Owner', report_trigger='Trigger',
               report_discharge='Discharge check', report_reference='Reference', report_no_tasks='No task board is available.',
               report_no_snapshot='No state snapshot is recorded.', report_no_roles='No sessions are active.',
               report_no_obligations='No open obligations are recorded.', report_lite='State and validation',
               report_state='State', report_validation='Validation', report_requirements='Requirements',
               report_requirement='Requirement', report_check='Check', report_no_validation='No validation command is recorded.',
               report_both='Plan and progress', report_context='Context', report_context_fallback='This export presents the recorded plan for {title} in plain language.', report_validation_recorded='A validation check is recorded for this plan.', report_pending_status='{count} recorded tasks are {status}.', report_continue_open='Continue the remaining recorded work before release.', report_choices_unavailable='No executive key choices are recorded.', report_state_counts='Current task states', report_purpose='Purpose', report_outcomes='Expected outcomes',
               report_scope_included='Included in this release', report_scope_deferred='Deferred or separate', report_roadmap='Road map',
               report_key_choices='Key choices', report_current_state='Current state', report_completed_summary='{done} of {total} recorded tasks are complete.',
               report_remaining_summary='{count} recorded tasks remain open or unfinished.', report_achievements='What is complete',
               report_open_work='Open work', report_next_steps='Next steps', report_evidence='Evidence and limits',
               report_dependency='Current dependency', report_not_recorded='Not recorded in the available summary.'),
    'es': dict(export_lede='Un documento autónomo para quien no conoce el proyecto: por qué importa el plan, dónde está el trabajo y qué sigue.', plan_desc='Propósito, resultados, alcance, hoja de ruta y decisiones clave.', progress_desc='Dónde está el trabajo: lo hecho, lo abierto y los siguientes pasos.', both_desc='El plan y su avance en un solo documento.', export_title='Comparte el plan', export='Exportar PDF', scope='Informe imprimible', plan='Plan', progress='Avance', both='Plan y avance',
               print='Exportar PDF', save_pdf='En el diálogo de impresión, elige Guardar como PDF.', print_error='No se pudo abrir el diálogo de impresión.',
               methodology_unavailable='Sin versión registrada (n/a)', report_planned_tasks='Tareas planificadas y dependencias',
               report_plan='Informe del plan', report_progress='Informe de avance', report_scope='Alcance', report_built='Generado',
               report_method='Metodología', report_printable='Informe imprimible', report_tasks='Avance de tareas',
               report_task='Tarea', report_what='Qué', report_status='Estado', report_brief='Brief',
               report_dependencies='Depende de', report_verification='Verificación', report_snapshot='Último estado registrado',
               report_roles='Sesiones abiertas', report_obligations='Obligaciones abiertas', report_obligation='Obligación', report_owner='Responsable', report_trigger='Disparador',
               report_discharge='Comprobación de cierre', report_reference='Referencia', report_no_tasks='No hay un tablero de tareas.',
               report_no_snapshot='No hay una instantánea de estado registrada.', report_no_roles='No hay sesiones activas.',
               report_no_obligations='No hay obligaciones abiertas registradas.', report_lite='Estado y validación',
               report_state='Estado', report_validation='Validación', report_requirements='Requisitos',
               report_requirement='Requisito', report_check='Comprobación', report_no_validation='No se registró un comando de validación.',
               report_both='Plan y avance', report_context='Contexto', report_context_fallback='Este informe presenta en lenguaje claro el plan registrado para {title}.', report_validation_recorded='Hay una comprobación de validación registrada para este plan.', report_pending_status='{count} tareas registradas están {status}.', report_continue_open='Continúa el trabajo registrado que queda antes de la publicación.', report_choices_unavailable='No hay decisiones ejecutivas clave registradas.', report_state_counts='Estados actuales de las tareas', report_purpose='Propósito', report_outcomes='Resultados esperados',
               report_scope_included='Incluido en esta versión', report_scope_deferred='Aplazado o separado', report_roadmap='Hoja de ruta',
               report_key_choices='Decisiones clave', report_current_state='Estado actual', report_completed_summary='{done} de {total} tareas registradas están completas.',
               report_remaining_summary='{count} tareas registradas siguen abiertas o incompletas.', report_achievements='Lo que está completo',
               report_open_work='Trabajo abierto', report_next_steps='Siguientes pasos', report_evidence='Evidencia y límites',
               report_dependency='Dependencia actual', report_not_recorded='No está registrado en el resumen disponible.')
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


def parse_requirement_rows(plan, reqs):
    """Extract the complete canonical criteria table without changing parse_requirements' tuple API."""
    lines = plan.splitlines()
    for index, line in enumerate(lines):
        if not line.lstrip().startswith('|') or index + 1 >= len(lines) or not table_rule(lines[index + 1]):
            continue
        header = [re.sub(r'\s+', ' ', value.strip().lower()) for value in cells(line)]
        required = ('criterion', 'required behavior', 'observable output/effect', 'boundary cases', 'valid alternatives')
        if not all(name in header for name in required):
            continue
        columns = {name: header.index(name) for name in required}
        rows = []
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].lstrip().startswith('|'):
            parts = cells(lines[cursor])
            cursor += 1
            if len(parts) <= columns['criterion']:
                continue
            match = re.fullmatch(r'`?(R\d+)`?', parts[columns['criterion']].strip())
            if not match:
                continue
            value = lambda name: parts[columns[name]] if columns[name] < len(parts) else ''
            rows.append(dict(id=match.group(1), behavior=value('required behavior'), output=value('observable output/effect'),
                             boundary=value('boundary cases'), alternative=value('valid alternatives')))
        if rows:
            return rows
    return [dict(id=rid, behavior=values[0], output=values[1], boundary='', alternative='')
            for rid, values in sorted(reqs.items(), key=lambda item: int(item[0][1:]))]


def parse_decisions(text):
    found = []
    boundaries = list(re.finditer(r'^#{1,2}\s+.+$', text, re.M))
    headings = []
    for boundary in boundaries:
        match = re.match(r'^##\s+(D-?\d+)(?:\s+(?:·|—|--)\s*(.*?))?\s*$', boundary.group(0))
        if match:
            headings.append((boundary, match))
    for _index, (boundary, match) in enumerate(headings):
        heading = (match.group(2) or '').strip()
        next_boundary = next((candidate.start() for candidate in boundaries if candidate.start() > boundary.start()), len(text))
        body = text[boundary.end():next_boundary].strip()
        parts = [part.strip() for part in heading.split(' · ')] if heading else []
        date = ''
        state = ''
        title_parts = list(parts)
        iso = re.compile(r'^\d{4}-\d{2}-\d{2}(?:T[^ ]+)?$')
        date_was_last = bool(title_parts and iso.fullmatch(title_parts[-1]))
        if title_parts and iso.fullmatch(title_parts[-1]):
            date = title_parts.pop()
        if date_was_last and len(title_parts) >= 2:
            state = title_parts.pop()
        # Older records put state before date; newer numeric headings often put the timestamp before the title.
        if not date and title_parts and iso.fullmatch(title_parts[0]):
            date = title_parts.pop(0)
        title = ' · '.join(title_parts).strip()
        found.append(dict(id=match.group(1), title=title, state=state, date=date, body=body))
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


def render_inline(text):
    """Render a small safe subset of inline Markdown after escaping workspace text."""
    value = esc(text)
    marker = 'TACKLEPLANVIEWCODETOKEN'
    while marker in value:
        marker += 'X'
    protected = {}

    def protect_code(match):
        token = '%s%d%s' % (marker, len(protected), marker)
        protected[token] = '<code>%s</code>' % match.group(1)
        return token

    value = re.sub(r'`([^`]+)`', protect_code, value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', value)
    value = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', value)
    for token, code in protected.items():
        value = value.replace(token, code)
    return value


def table_rule(line):
    parts = cells(line)
    return bool(parts) and all(re.fullmatch(r':?-{3,}:?', part) for part in parts)


def render_markdown(source):
    """Render headings, lists, fenced code, tables, quotes, and paragraphs safely."""
    lines = source.splitlines()
    out, at = [], 0

    def starts_block(index):
        line = lines[index]
        return (bool(re.match(r'^\s*```', line)) or bool(re.match(r'^#{1,6}\s+', line))
                or bool(re.match(r'^\s*(?:[-+*]\s+|\d+[.)]\s+|>\s?)', line))
                or (line.lstrip().startswith('|') and index + 1 < len(lines) and table_rule(lines[index + 1])))

    def list_marker(source_line):
        return re.match(r'^([ \t]*)(?:([-+*])|(\d+)[.)])[ \t]+(.*)$', source_line)

    def render_list(index, indent):
        first = list_marker(lines[index])
        tag = 'ol' if first.group(3) is not None else 'ul'
        start = first.group(3) or '1'
        items = []
        while index < len(lines):
            match = list_marker(lines[index])
            if not match:
                break
            current_indent = len(match.group(1).expandtabs(4))
            if current_indent < indent:
                break
            if current_indent > indent:
                if not items:
                    break
                nested, index = render_list(index, current_indent)
                items[-1] = items[-1][:-5] + nested + '</li>'
                continue
            match_tag = 'ol' if match.group(3) is not None else 'ul'
            if match_tag != tag:
                break
            items.append('<li>%s</li>' % render_inline(match.group(4)))
            index += 1
        start_attr = ' start="%s"' % start if tag == 'ol' and start != '1' else ''
        return '<%s%s>%s</%s>' % (tag, start_attr, ''.join(items), tag), index

    while at < len(lines):
        line = lines[at]
        if not line.strip():
            at += 1
            continue
        fence = re.match(r'^\s*(`{3,}|~{3,})(.*)$', line)
        if fence:
            marker = fence.group(1)
            at += 1
            code = []
            while at < len(lines):
                closing = re.match(r'^\s*([`~]+)\s*$', lines[at])
                if (closing and all(char == marker[0] for char in closing.group(1))
                        and len(closing.group(1)) >= len(marker)):
                    break
                code.append(lines[at])
                at += 1
            if at < len(lines):
                at += 1
            language = fence.group(2).strip()
            klass = ' class="language-%s"' % esc(language) if re.fullmatch(r'[A-Za-z0-9_-]+', language) else ''
            out.append('<pre><code%s>%s</code></pre>' % (klass, esc('\n'.join(code))))
            continue
        heading = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
        if heading:
            level = len(heading.group(1))
            heading_text = re.sub(r'\s+#+\s*$', '', heading.group(2))
            out.append('<h%d>%s</h%d>' % (level, render_inline(heading_text), level))
            at += 1
            continue
        if line.lstrip().startswith('|') and at + 1 < len(lines) and table_rule(lines[at + 1]):
            header = cells(line)
            at += 2
            rows = []
            while at < len(lines) and lines[at].lstrip().startswith('|'):
                rows.append(cells(lines[at]))
                at += 1
            th = ''.join('<th scope="col">%s</th>' % render_inline(value) for value in header)
            body = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % render_inline(value) for value in row)
                           for row in rows)
            out.append('<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (th, body))
            continue
        list_start = list_marker(line)
        if list_start:
            list_html, at = render_list(at, len(list_start.group(1).expandtabs(4)))
            out.append(list_html)
            continue
        if re.match(r'^\s*>', line):
            quotes = []
            while at < len(lines) and re.match(r'^\s*>', lines[at]):
                quotes.append(re.sub(r'^\s*>\s?', '', lines[at]))
                at += 1
            out.append('<blockquote><p>%s</p></blockquote>' % '<br>'.join(render_inline(value) for value in quotes))
            continue
        paragraph = [line]
        at += 1
        while at < len(lines) and lines[at].strip() and not starts_block(at):
            paragraph.append(lines[at])
            at += 1
        out.append('<p>%s</p>' % '<br>'.join(render_inline(value) for value in paragraph))
    return ''.join(out)


def plan_report_source(plan):
    gate = ''
    kept = []
    initial = True
    for line in plan.splitlines():
        if initial and not line.strip():
            kept.append(line)
            continue
        if initial and re.fullmatch(r'\s*Gate:\s*Lite\s*', line):
            gate = '<p class="report-gate"><span class="report-gate-label">Gate</span><span>Lite</span></p>'
            initial = False
            continue
        initial = False
        kept.append(line)
    return gate + render_markdown('\n'.join(kept))


def open_obligations(board):
    found, in_section, columns = [], False, None
    for line in board.splitlines():
        heading = re.match(r'^#{1,6}\s+(.+)$', line)
        if heading:
            in_section = heading.group(1).strip().lower() == 'obligations'
            columns = None
            continue
        if not in_section or not line.lstrip().startswith('|'):
            continue
        parts = cells(line)
        if columns is None:
            lowered = [value.lower() for value in parts]
            if 'obligation' in lowered and 'state' in lowered and 'what' in lowered:
                columns = {name: index for index, name in enumerate(lowered)}
            continue
        if table_rule(line) or len(parts) <= max(columns.values()):
            continue
        if parts[columns['state']].strip().lower() != 'open':
            continue
        found.append({name: parts[index] if index < len(parts) else '' for name, index in columns.items()})
    return found


def report_table(headers, rows):
    head = '<tr>%s</tr>' % ''.join('<th scope="col">%s</th>' % esc(value) for value in headers)
    body = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % esc(value) for value in row) for row in rows)
    return '<table><thead>%s</thead><tbody>%s</tbody></table>' % (head, body)


def report_section(ident, heading, title, scope, stamp, method, content, attrs=''):
    metadata = '<dl class="report-meta"><dt>%s</dt><dd>%s</dd><dt>%s</dt><dd>%s</dd><dt>%s</dt><dd>%s</dd></dl>' % (
        esc(scope[0]), esc(scope[1]), esc(stamp[0]), esc(stamp[1]), esc(method[0]), esc(method[1]))
    return ('<section class="print-report" id="%s"%s><header class="report-head"><p class="report-kicker">%s</p>'
            '<h1>%s</h1>%s</header><div class="report-body">%s</div></section>') % (
        ident, attrs, esc(heading), esc(title), metadata, content)


def presentation_overview(summary, objective, ui):
    """The curated outcomes and milestones; a reading aid that never becomes a source of facts or progress."""
    if not summary or not (summary['outcomes'] or summary['milestones']):
        return ''
    cards = ''.join('<article class="outcome-card"><span class="outcome-index">%02d</span><h3 class="outcome-title">%s</h3>'
                    '<p class="outcome-text">%s</p></article>' % (index, esc(item['title']), esc(item['text']))
                    for index, item in enumerate(summary['outcomes'], 1))
    outcome_html = '<div class="outcome-grid">%s</div>' % cards if cards else ''
    timeline = ''.join('<li class="milestone-item"><span class="milestone-key">%s</span><span class="milestone-text">%s</span></li>' %
                       (esc(key), esc(text)) for key, text in summary['milestones'].items())
    milestone_html = ('<div class="milestones"><h3>%s</h3><ol class="milestone-track">%s</ol></div>' %
                      (esc(ui['milestones']), timeline)) if timeline else ''
    return ('<section class="sec" id="overview"><header class="sec-head"><h2>%s</h2><p class="sec-lede">%s</p></header>%s%s'
            '<p class="source-note">%s</p></section>' %
            (esc(ui['outcomes']), esc(ui['outcomes_lede']), outcome_html, milestone_html, esc(ui['source_note'])))


def requirements_section(rows, cover, focused, ui):
    cards = []
    for row in rows:
        ident = row['id']
        ownership = cover.get(ident, [])
        owners = ''.join('<a class="ref" href="#task-%s">%s</a>' % (esc(task), esc(task)) for task in ownership) or \
            '<span class="none">%s</span>' % esc(ui['no_task'])
        fields = (
            ('behavior', ui['behavior'], row.get('behavior', '')),
            ('output', ui['output'], row.get('output', '')),
            ('boundary', ui['boundary'], row.get('boundary', '')),
            ('alternative', ui['alternative'], row.get('alternative', '')))
        details = ''.join('<div class="req-field req-%s"><dt>%s</dt><dd>%s</dd></div>' %
                          (name, esc(label), render_inline(value) if value else '–') for name, label, value in fields)
        cards.append('<article class="requirement-card%s" id="requirement-%s" data-requirement="%s" data-tasks="%s">'
                     '<button type="button" class="requirement-id req-toggle" aria-pressed="false" aria-label="%s">%s</button>'
                     '<p class="req-purpose">%s</p><p class="req-owner"><span class="req-k">%s</span>%s</p>'
                     '<details class="req-evidence"><summary>%s</summary><dl>%s</dl></details></article>' %
                     ('' if ownership or focused else ' is-uncovered', esc(ident), esc(ident), esc(' '.join(ownership)),
                      esc(ui['req_toggle'].format(id=ident)), esc(ident), render_inline(row.get('behavior', '')),
                      esc(ui['covered_by']), owners, esc(ui['source_details']), details))
    body = ''.join(cards) if cards else '<p class="empty">%s</p>' % esc(ui['no_requirements'])
    return ('<section class="sec" id="requirements"><header class="sec-head"><h2>%s</h2><p class="sec-lede">%s</p></header>'
            '<div class="requirement-list">%s</div></section>' % (esc(ui['requirements']), esc(ui['requirements_intro']), body))


def technical_details(reqs, cover, fields, tasks, decisions, focused, ui):
    """Complete source collections in native disclosures, independent of view filters."""
    coverage = []
    for ident, (behavior, check) in reqs.items():
        owners = ', '.join('<a href="#task-%s">%s</a>' % (esc(task), esc(task)) for task in cover.get(ident, []))
        ownership = '' if focused else '<div><dt>%s</dt><dd>%s</dd></div>' % (esc(ui['covered_by']), owners or esc(ui['no_task']))
        coverage.append('<article class="technical-record"><h4 class="mono">%s</h4><dl>'
                        '<div><dt>%s</dt><dd>%s</dd></div><div><dt>%s</dt><dd>%s</dd></div>%s</dl></article>' % (
                            esc(ident), esc(ui['behavior']), render_inline(behavior),
                            esc(ui['check_lite'] if focused else ui['check']), render_inline(check) if check else '—', ownership))
    validation = '<p class="technical-validation"><b>%s</b>: %s</p>' % (esc(ui['validation']), esc(fields['validation'])) if focused and fields.get('validation') else ''
    collections = [(ui['coverage'], ui['technical_coverage_note'], len(reqs),
                    '<div class="technical-record-grid">%s</div>%s' % (''.join(coverage), validation))]
    if tasks:
        records = []
        for task in tasks:
            records.append('<article class="technical-record" data-record-task="%s"><h4><a href="#task-%s"><span class="mono">%s</span> · %s</a></h4><dl>'
                           '<div><dt>%s</dt><dd>%s</dd></div><div><dt>%s</dt><dd><code>%s</code></dd></div>'
                           '<div><dt>%s</dt><dd>%s</dd></div></dl></article>' % (
                               esc(task['id']), esc(task['id']), esc(task['id']), esc(task['title']),
                               esc(ui['status']), esc(task['status']), esc(ui['brief']), esc(task['brief']),
                               esc(ui['verification']), render_inline(task['verification']) if task['verification'] else '—'))
        collections.append((ui['tasks'], ui['technical_tasks_note'], len(tasks), '<div class="technical-record-grid">%s</div>' % ''.join(records)))
    decision_rows = ''.join('<tr><th scope="row"><a href="#decision-record-%s">%s</a></th><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        esc(item['id']), esc(item['id']), esc(item['title']), esc(item['state'] or ui['unknown']), esc(item['date'] or ui['unknown'])) for item in decisions)
    decision_table = ('<div class="tw" tabindex="0" role="region" aria-label="%s"><table><thead><tr><th scope="col">%s</th>'
                      '<th scope="col">%s</th><th scope="col">%s</th><th scope="col">%s</th></tr></thead><tbody>%s</tbody></table></div>') % (
                          esc(ui['decisions']), esc(ui['decision']), esc(ui['record_title']), esc(ui['state']), esc(ui['date']), decision_rows)
    collections.append((ui['decisions'], ui['technical_decisions_note'], len(decisions), decision_table))
    body = ''.join('<details class="technical-collection"><summary><span>%s</span><span class="technical-count">%s</span></summary>'
                   '<div class="technical-collection-body"><p class="technical-collection-note">%s</p>%s</div></details>' % (
                       esc(title), esc(ui['technical_count'].format(count=count)), esc(note), content)
                   for title, note, count, content in collections)
    return '<details class="technical-details"><summary>%s</summary><div class="technical-content"><p>%s</p>%s</div></details>' % (
        esc(ui['technical']), esc(ui['technical_note']), body)


def decisions_section(summary, decisions, ui):
    story = []
    if summary:
        for item in summary['decisions']:
            date = '<time class="decision-date">%s</time>' % esc(item['date']) if item['date'] else ''
            story.append('<li class="decision-card">%s<p class="decision-text">%s</p></li>' % (date, esc(item['text'])))
    more = ('<button type="button" class="tool story-more" data-more="%s" data-less="%s" aria-expanded="false" hidden>%s</button>' % (
        esc(ui['show_all'].format(count=len(story))), esc(ui['show_less']), esc(ui['show_all'].format(count=len(story))))) if len(story) > 6 else ''
    story_html = ('<div class="decision-story-wrap"><h3 class="decision-story-heading">%s</h3><ol class="decision-story">%s</ol>%s</div>' %
                  (esc(ui['decision_story']), ''.join(story), more)) if story else ''
    records = []
    for item in decisions:
        state = item.get('state') or ui['unknown']
        date = item.get('date') or ui['unknown']
        body_text = item.get('body', '')
        raw = render_markdown(body_text) if body_text.strip() else '<p>–</p>'
        source = ('<details class="decision-source"><summary>%s</summary><pre>%s</pre></details>' %
                  (esc(ui['raw_record']), esc(body_text))) if body_text.strip() else ''
        search = esc(' '.join((item.get('id', ''), item.get('title', ''), item.get('state', ''), item.get('date', ''), item.get('body', ''))))
        records.append('<article class="decision-record" id="decision-record-%s" data-decision-id="%s" data-search="%s">'
                       '<div class="decision-record-head"><span class="requirement-id">%s</span><time class="decision-date">%s</time>'
                       '<span class="decision-state">%s</span></div><h4 class="decision-title">%s</h4>'
                       '<details class="decision-raw"><summary>%s</summary><div>%s</div></details></article>' %
                       (esc(item['id']), esc(item['id']), search, esc(item['id']), esc(date), esc(state), esc(item.get('title', '') or ui['unknown']),
                        esc(ui['decision_record']), '<div class="decision-text">%s</div>%s' % (raw, source)))
    controls = ('<div class="decision-search" hidden><label for="plan-decision-search">%s</label><input type="search" id="plan-decision-search" '
                'placeholder="%s" autocomplete="off"><button type="button" class="tool" id="plan-decision-clear">%s</button>'
                '<p id="plan-decision-results" role="status" aria-live="polite">%s</p></div>') % (
                    esc(ui['search_decisions']), esc(ui['search_placeholder']), esc(ui['clear_search']), esc(ui['search_results']))
    archive_label = '%s · %s' % (ui['canonical_archive'], ui['decision_count'].format(count=len(decisions)))
    archive = '<details class="decision-archive"><summary>%s</summary>%s<div class="decision-records" data-empty="%s">%s</div></details>' % (
        esc(archive_label), controls, esc(ui['unknown']), ''.join(records))
    return ('<section class="sec" id="decisions"><header class="sec-head"><h2>%s</h2><p class="sec-lede">%s</p></header>%s%s</section>' %
            (esc(ui['decisions']), esc(ui['decisions_intro']), story_html, archive))


def executive_excerpt(value, limit=280):
    text = re.sub(r'[`*_>#]+', ' ', _summary_text(value))
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(?<!\w)(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+', '', text)
    text = re.sub(r'\b[0-9a-f]{8,}\b', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    return text if len(text) <= limit else text[:limit].rsplit(' ', 1)[0] + '…'


def executive_section(label, content):
    return '<section class="report-section"><h2>%s</h2>%s</section>' % (esc(label), content)


def executive_pairs(items):
    if not items:
        return ''
    return '<div class="executive-grid">%s</div>' % ''.join(
        '<article class="executive-item"><h3>%s</h3><p>%s</p></article>' %
        (esc(item['title']), esc(item['text'])) for item in items)


def executive_bullets(items):
    return '<ul>%s</ul>' % ''.join('<li>%s</li>' % esc(item) for item in items)


def executive_shared(export_summary, summary, title, objective, ui, export_ui):
    source = export_summary or {}
    report_title = source.get('title') or (summary.get('title') if summary else '') or title
    context = source.get('context') or export_ui['report_context_fallback'].format(title=report_title)
    purpose = source.get('purpose') or (summary.get('objective') if summary else '') or objective
    body = '<p>%s</p>' % esc(context)
    if purpose:
        body += '<p><strong>%s:</strong> %s</p>' % (esc(export_ui['report_purpose']), esc(purpose))
    return report_title, executive_section(export_ui['report_context'], body)


def executive_plan_story(export_summary, summary, decisions, title, objective, ui, export_ui):
    source = export_summary or {}
    plan = source.get('plan', {})
    parts = []
    themes = plan.get('themes') or ([dict(title=item['title'], text=item['text']) for item in summary['outcomes']] if summary else [])
    if themes:
        parts.append(executive_section(export_ui['report_outcomes'], executive_pairs(themes)))
    elif objective:
        parts.append(executive_section(export_ui['report_outcomes'], '<p>%s</p>' % esc(objective)))
    included, deferred = plan.get('included', []), plan.get('deferred', [])
    if included:
        parts.append(executive_section(export_ui['report_scope_included'], executive_bullets(included)))
    if deferred:
        parts.append(executive_section(export_ui['report_scope_deferred'], executive_bullets(deferred)))
    roadmap = plan.get('roadmap', [])
    if not roadmap and summary:
        roadmap = [dict(title=key, text=text) for key, text in summary['milestones'].items()]
    if roadmap:
        parts.append(executive_section(export_ui['report_roadmap'], executive_pairs(roadmap)))
    choices = plan.get('key_choices', [])
    if choices:
        parts.append(executive_section(export_ui['report_key_choices'], executive_pairs(choices)))
    else:
        parts.append(executive_section(export_ui['report_key_choices'], '<p>%s</p>' % esc(export_ui['report_choices_unavailable'])))
    if not parts:
        parts.append(executive_section(export_ui['report_outcomes'], '<p>%s</p>' % esc(export_ui['report_not_recorded'])))
    return ''.join(parts)


def executive_task_state_counts(tasks):
    counts = {}
    for task in tasks:
        state = task.get('status', '')
        counts[state] = counts.get(state, 0) + 1
    return counts


def executive_progress_story(export_summary, summary, fields, tasks, focused, ui, export_ui):
    source = export_summary or {}
    progress = source.get('progress', {})
    parts = []
    current = []
    if tasks:
        done = sum(1 for task in tasks if task['status'] == 'Complete')
        remaining = len(tasks) - done
        current.append(export_ui['report_completed_summary'].format(done=done, total=len(tasks)))
        if remaining:
            current.append(export_ui['report_remaining_summary'].format(count=remaining))
    elif focused:
        state = fields.get('state', '')
        if state:
            current.append('%s: %s' % (export_ui['report_state'], state))
        current.append(export_ui['report_no_tasks'])
    else:
        current.append(export_ui['report_no_tasks'])
    figure = ''
    if tasks:
        done = sum(1 for task in tasks if task['status'] == 'Complete')
        figure = '<div class="report-figure" aria-hidden="true"><p class="report-count"><b>%d</b><span>/%d</span></p><p class="report-strip">%s</p></div>' % (
            done, len(tasks), ''.join('<i class="s-%s"></i>' % STATE_CLASS.get(task['status'], 'draft') for task in tasks))
    current_body = '<div class="executive-progress">%s%s' % (figure, executive_bullets(current))
    if tasks:
        state_labels = ['%s: %d' % (ui['states'].get(state, state), count)
                       for state, count in executive_task_state_counts(tasks).items()]
        current_body += '<p class="executive-note"><strong>%s:</strong> %s</p>' % (
            esc(export_ui['report_state_counts']), esc(' · '.join(state_labels)))
    current_body += '</div>'
    parts.append(executive_section(export_ui['report_current_state'], current_body))
    achievements = progress.get('achievements', [])
    if not achievements and tasks:
        done = sum(1 for task in tasks if task['status'] == 'Complete')
        if done:
            achievements = [dict(title=export_ui['report_achievements'], text=export_ui['report_completed_summary'].format(done=done, total=len(tasks)))]
    if achievements:
        parts.append(executive_section(export_ui['report_achievements'], executive_pairs(achievements)))
    open_work = progress.get('open_work', [])
    open_tasks = [task for task in tasks if task['status'] != 'Complete']
    if not open_work and open_tasks:
        status_counts = {}
        for task in open_tasks:
            status = ui['states'].get(task['status'], task['status'])
            status_counts[status] = status_counts.get(status, 0) + 1
        open_work = [dict(title=status, text=export_ui['report_pending_status'].format(count=count, status=status))
                     for status, count in status_counts.items()]
    if open_work:
        parts.append(executive_section(export_ui['report_open_work'], executive_pairs(open_work)))
    dependency = progress.get('dependency')
    if dependency:
        parts.append(executive_section(export_ui['report_dependency'], '<p>%s</p>' % esc(dependency)))
    next_steps = progress.get('next', [])
    if not next_steps and summary and summary.get('next'):
        next_steps = summary['next'][:3]
    if not next_steps and open_tasks:
        next_steps = [export_ui['report_continue_open']]
    if next_steps:
        parts.append(executive_section(export_ui['report_next_steps'], executive_bullets(next_steps)))
    evidence = progress.get('evidence', '')
    if not evidence and fields.get('validation'):
        evidence = export_ui['report_validation_recorded']
    meaning = progress.get('meaning')
    if evidence or meaning:
        evidence_body = ''
        if meaning:
            evidence_body += '<p>%s</p>' % esc(meaning)
        if evidence:
            evidence_body += '<p>%s</p>' % esc(evidence)
        parts.append(executive_section(export_ui['report_evidence'], evidence_body))
    return ''.join(parts)


def printable_reports(plan, focused, fields, reqs, requirement_rows, decisions, summary, export_summary, tasks, working, board, snapshot, stamp, method, title, ui, export_ui):
    plan_scope = (export_ui['report_scope'], export_ui['plan'])
    progress_scope = (export_ui['report_scope'], export_ui['progress'])
    built = (export_ui['report_built'], stamp)
    methodology = (export_ui['report_method'], method)
    report_title, shared = executive_shared(export_summary, summary, title, objective_of(plan), ui, export_ui)
    plan_story = executive_plan_story(export_summary, summary, decisions, title, objective_of(plan), ui, export_ui)
    progress_story = executive_progress_story(export_summary, summary, fields, tasks, focused, ui, export_ui)
    compact_source = export_summary or {}
    compact_context_text = compact_source.get('context') or export_ui['report_context_fallback'].format(title=report_title)
    compact_purpose = compact_source.get('purpose') or (summary.get('objective') if summary else '') or objective_of(plan)
    compact_context = '<p>%s%s</p>' % (esc(compact_context_text), (' <strong>%s:</strong> %s' % (esc(export_ui['report_purpose']), esc(compact_purpose))) if compact_purpose else '')
    total = len(tasks)
    completed = sum(1 for task in tasks if task['status'] == 'Complete')
    state_counts_json = esc(json.dumps(executive_task_state_counts(tasks), ensure_ascii=False, separators=(',', ':')))
    progress_attrs = ' data-total="%d" data-completed="%d" data-state-counts="%s"' % (total, completed, state_counts_json)
    plan_html = report_section('print-report-plan', export_ui['report_plan'], report_title, plan_scope, built, methodology, shared + plan_story)
    progress_html = report_section('print-report-progress', export_ui['report_progress'], report_title, progress_scope, built, methodology,
                                   executive_section(export_ui['report_context'], compact_context) + progress_story, progress_attrs)
    part = '<p class="report-part">%s</p>' % esc(export_ui['progress'])
    both_html = report_section('print-report-both', export_ui['report_both'], report_title, (export_ui['report_scope'], export_ui['both']), built, methodology,
                               shared + plan_story + part + progress_story, progress_attrs)
    return plan_html + progress_html + both_html

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


def isotonic(values):
    """The non-decreasing sequence closest to values in squared distance (pool adjacent violators)."""
    blocks = []
    for value in values:
        blocks.append([value, 1])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
            total, count = blocks.pop()
            blocks[-1][0] += total
            blocks[-1][1] += count
    out = []
    for total, count in blocks:
        out += [total / count] * count
    return out


def rounded_path(points, radius=7):
    """An orthogonal polyline as a path whose corners turn on short quadratic curves."""
    pts = [points[0]]
    for p in points[1:]:
        if abs(p[0] - pts[-1][0]) > 0.01 or abs(p[1] - pts[-1][1]) > 0.01:
            pts.append(p)
    clean = [pts[0]]
    for k in range(1, len(pts) - 1):
        a, b, c = clean[-1], pts[k], pts[k + 1]
        if (abs(a[0] - b[0]) < 0.01 and abs(b[0] - c[0]) < 0.01) or (abs(a[1] - b[1]) < 0.01 and abs(b[1] - c[1]) < 0.01):
            continue
        clean.append(b)
    if len(pts) > 1:
        clean.append(pts[-1])

    def toward(p, q, dist):
        length = abs(q[0] - p[0]) + abs(q[1] - p[1])
        return (p[0] + (q[0] - p[0]) * dist / length, p[1] + (q[1] - p[1]) * dist / length) if length else p

    d = 'M%.1f %.1f' % clean[0]
    for k in range(1, len(clean) - 1):
        a, b, c = clean[k - 1], clean[k], clean[k + 1]
        r = min(radius, (abs(b[0] - a[0]) + abs(b[1] - a[1])) / 2, (abs(c[0] - b[0]) + abs(c[1] - b[1])) / 2)
        enter, leave = toward(b, a, r), toward(b, c, r)
        d += ' L%.1f %.1f Q%.1f %.1f %.1f %.1f' % (enter[0], enter[1], b[0], b[1], leave[0], leave[1])
    if len(clean) > 1:
        d += ' L%.1f %.1f' % clean[-1]
    return d


def status_glyph(klass, x, y, size=10):
    """The state mark used across the page: filled when complete, half filled when active, open otherwise."""
    frame = '<rect class="glyph-frame" x="%.1f" y="%.1f" width="%d" height="%d"/>' % (x, y, size, size)
    if klass == 'done':
        return frame + '<rect class="glyph-fill" x="%.1f" y="%.1f" width="%d" height="%d"/>' % (x, y, size, size)
    if klass == 'prog':
        return frame + '<rect class="glyph-fill" x="%.1f" y="%.1f" width="%.1f" height="%d"/>' % (x, y, size / 2, size)
    if klass in ('block', 'wait'):
        return frame + '<rect class="glyph-fill" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (x + size * .3, y + size * .3, size * .4, size * .4)
    return frame


def choose_layout(ids, stage, edges):
    """Keep the earliest stages, or pull sources toward the work that needs them, whichever crosses fewer arrows."""
    kids = {i: [b for a, b in edges if a == i] for i in ids}
    late = {}

    def latest(i):
        if i not in late:
            late[i] = min(latest(k) for k in kids[i]) - 1 if kids[i] else (max(stage.values()) if stage[i] else 0)
        return late[i]

    options = [(stage, layered(ids, stage, edges)), ({i: latest(i) for i in ids}, None)]
    options[1] = (options[1][0], layered(ids, options[1][0], edges))
    chosen, (order, chains, _) = min(options, key=lambda o: o[1][2])
    return chosen, order, chains


def graph_svg(tasks, layout, live, ui):
    """Stage columns read left to right. Boxes settle beside the work they connect to, an arrow that skips a stage
    passes through the stages between its ends, and each arrow turns in the gutter after its source on a rail
    shared only by arrows of that source, so the picture keeps few bends and few crossings."""
    title = {t['id']: t['title'] for t in tasks}
    state = {t['id']: t['status'] for t in tasks}
    _, order, chains = layout
    node_w, dummy_h, gap_node, gap_dummy, head, pad = 192, 8, 18, 8, 64, 24
    lines_of = {t['id']: wrap(t['title'], 23, 3) for t in tasks}
    node_h = 40 + 17 * max([len(lines) for lines in lines_of.values()] or [1])
    size = lambda n: node_h if n in title else dummy_h
    gap = lambda a, b: gap_node if (a in title or b in title) else gap_dummy
    left, right = {}, {}
    for chain in chains.values():
        for u, v in zip(chain, chain[1:]):
            right.setdefault(u, []).append(v)
            left.setdefault(v, []).append(u)
    top = {}
    for col in order:
        y = 0
        for k, n in enumerate(col):
            top[n] = y
            y += size(n) + (gap(n, col[k + 1]) if k + 1 < len(col) else 0)
    center = lambda n: top[n] + size(n) / 2

    def settle(col, wants):
        offsets, y = [], 0
        for k, n in enumerate(col):
            offsets.append(y)
            y += size(n) + (gap(n, col[k + 1]) if k + 1 < len(col) else 0)
        fitted = isotonic([wants.get(n, center(n)) - size(n) / 2 - offsets[k] for k, n in enumerate(col)])
        for k, n in enumerate(col):
            top[n] = fitted[k] + offsets[k]

    def wants_from(col, sides):
        found = {}
        for n in col:
            near = sorted(center(m) for side in sides for m in side.get(n, []))
            if near:
                mid = len(near) // 2
                found[n] = near[mid] if len(near) % 2 else (near[mid - 1] + near[mid]) / 2
        return found

    rounds = 6 if len(top) <= 400 else 2
    for _ in range(rounds):
        for col in order[1:]:
            settle(col, wants_from(col, (left,)))
        for col in reversed(order[:-1]):
            settle(col, wants_from(col, (right,)))
    for col in order:
        settle(col, wants_from(col, (left, right)))
    position = {n: (c, k) for c, col in enumerate(order) for k, n in enumerate(col)}

    def fits(n, y):
        c, k = position[n]
        col = order[c]
        if k > 0 and y < top[col[k - 1]] + size(col[k - 1]) + gap(col[k - 1], n):
            return False
        return not (k + 1 < len(col) and y + size(n) + gap(n, col[k + 1]) > top[col[k + 1]])

    for chain in sorted(chains.values(), key=len, reverse=True):
        inner = chain[1:-1]
        for anchor in ((center(chain[0]), center(chain[-1]), center(inner[0])) if inner else ()):
            if all(fits(n, anchor - dummy_h / 2) for n in inner):
                for n in inner:
                    top[n] = anchor - dummy_h / 2
                break
    low = min(top.values())
    for n in top:
        top[n] += head + pad - low
    height = max(top[n] + size(n) for n in top) + pad
    column_of = {n: c for c, col in enumerate(order) for n in col}
    outgoing, incoming = {}, {}
    for chain in chains.values():
        for u, v in zip(chain, chain[1:]):
            outgoing.setdefault(u, []).append(v)
            incoming.setdefault(v, []).append(u)

    def port(n, other, leaving):
        """A single-link side meets the other end level when the box allows it; shared sides use the middle."""
        own = outgoing.get(n, []) if leaving else incoming.get(n, [])
        if n in title and len(own) == 1 and len((incoming if leaving else outgoing).get(other, [])) <= 1:
            wanted = center(other) if other not in title else top[other] + node_h / 2
            if top[n] + 14 <= wanted <= top[n] + node_h - 14:
                return wanted
        return center(n)

    ends = {}
    for chain in chains.values():
        for u, v in zip(chain, chain[1:]):
            y1 = port(u, v, True)
            y2 = port(v, u, False)
            if u in title and v in title and abs(y1 - center(v)) < 0.5:
                y2 = y1
            if v in title and u in title and abs(y2 - center(u)) < 0.5:
                y1 = y2
            ends[(u, v)] = (y1, y2)
    gutters = {}
    for (u, v), (y1, y2) in ends.items():
        if abs(y1 - y2) >= 0.5:
            key = (u, y1, 'down' if y2 > y1 else 'up')
            gutters.setdefault(column_of[u], {}).setdefault(key, []).append(y2)
    widths = []
    for c in range(len(order)):
        rails = len(gutters.get(c, {}))
        step = 11 if rails <= 24 else max(3, 264 / rails)
        widths.append(max(62, (rails + 1) * step) if c < len(order) - 1 else 0)
    xs, x = [], pad
    for c in range(len(order)):
        xs.append(x)
        x += node_w + widths[c]
    width = x - (widths[-1] if widths else 0) + pad
    rail_x = {}
    for c, groups in gutters.items():
        ups = sorted((key for key in groups if key[2] == 'up'), key=lambda key: (key[1], min(groups[key])))
        downs = sorted((key for key in groups if key[2] == 'down'), key=lambda key: (-key[1], -max(groups[key])))
        ordered = ups + downs
        for k, key in enumerate(ordered):
            rail_x[(c, key)] = xs[c] + node_w + (k + 1) * widths[c] / (len(ordered) + 1)
    out = ['<svg class="flow-svg" viewBox="0 0 %d %d" width="%d" height="%d" role="group" aria-label="%s">'
           '<defs><marker id="arrow" viewBox="0 0 8 8" refX="7.4" refY="4" markerWidth="7" markerHeight="7" orient="auto">'
           '<path class="arrowhead" d="M 0 0.6 L 8 4 L 0 7.4 z"/></marker><marker id="arrow-up" viewBox="0 0 8 8" refX="7.4" refY="4" markerWidth="7" markerHeight="7" orient="auto">'
           '<path class="arrowhead-up" d="M 0 0.6 L 8 4 L 0 7.4 z"/></marker><marker id="arrow-down" viewBox="0 0 8 8" refX="7.4" refY="4" markerWidth="7" markerHeight="7" orient="auto">'
           '<path class="arrowhead-down" d="M 0 0.6 L 8 4 L 0 7.4 z"/></marker></defs>' % (width, height, width, height, esc(ui['graph']))]
    for c, col in enumerate(order):
        done = sum(1 for n in col if n in title and state[n] == 'Complete')
        count = sum(1 for n in col if n in title)
        out.append('<g class="stage" data-stage="%d"><rect class="band" x="%.1f" y="0" width="%d" height="%d"/>'
                   '<text class="band-h" x="%.1f" y="27">%s</text><text class="band-c" x="%.1f" y="45">%s</text></g>' % (
                       c + 1, xs[c] - 12, node_w + 24, height, xs[c], esc(ui['stage'].format(n=c + 1)), xs[c],
                       esc(ui['stage_count'].format(done=done, total=count))))
    for (a, b), chain in chains.items():
        y_start = ends[(chain[0], chain[1])][0]
        points = [(xs[column_of[a]] + node_w, y_start)]
        for u, v in zip(chain, chain[1:]):
            y1, y2 = ends[(u, v)]
            c = column_of[u]
            if abs(y1 - y2) >= 0.5:
                rx = rail_x[(c, (u, y1, 'down' if y2 > y1 else 'up'))]
                points += [(rx, y1), (rx, y2)]
            if v in title:
                points.append((xs[column_of[v]], y2))
            else:
                points += [(xs[column_of[v]], y2), (xs[column_of[v]] + node_w, y2)]
        out.append('<path class="edge %s" data-from="%s" data-to="%s" d="%s" marker-end="url(#arrow)"/>' % (
            'met' if state[a] == 'Complete' else 'open', a, b, rounded_path(points)))
    for t in tasks:
        n = t['id']
        x, y = xs[column_of[n]], top[n]
        klass = STATE_CLASS.get(t['status'], 'draft')
        lines = lines_of[n]
        text = ''.join('<tspan x="%.1f" dy="%d">%s</tspan>' % (x + 14, 0 if k == 0 else 17, esc(line)) for k, line in enumerate(lines))
        label = '%s · %s · %s' % (n, t['title'], ui['states'].get(t['status'], t['status']))
        out.append('<g class="node s-%s" data-task="%s" data-status="%s"%s tabindex="0" role="button" aria-label="%s"><title>%s</title>'
                   '<rect class="node-box" x="%.1f" y="%.1f" width="%d" height="%d"/><g class="glyph">%s</g>'
                   '<text class="nid" x="%.1f" y="%.1f">%s</text><text class="nt" x="%.1f" y="%.1f">%s</text></g>' % (
                       klass, n, esc(t['status']), ' data-live="true"' if n in live else '', esc(label), esc(label),
                       x, y, node_w, node_h, status_glyph(klass, x + node_w - 24, y + 14) +
                       ('<circle class="live-dot" cx="%.1f" cy="%.1f" r="4"/>' % (x + node_w - 40, y + 19) if n in live else ''),
                       x + 14, y + 24, n, x + 14, y + 45, text))
    out.append('</svg>')
    return ''.join(out)


def stage_list(tasks, stage, edges, ui):
    """The same stages as a reading list: each task with what it needs, for narrow screens and readers without the picture."""
    by_stage = {}
    for t in tasks:
        by_stage.setdefault(stage[t['id']], []).append(t)
    needs = {t['id']: sorted(set(t['deps']), key=lambda i: int(i[2:])) for t in tasks}
    groups = []
    for number in sorted(by_stage):
        listed = by_stage[number]
        done = sum(1 for t in listed if t['status'] == 'Complete')
        rows = []
        for t in listed:
            klass = STATE_CLASS.get(t['status'], 'draft')
            need = ', '.join('<span class="nb">%s</span>' % i for i in needs[t['id']]) or esc(ui['nothing'])
            rows.append('<li><a class="stage-task s-%s" href="#task-%s" data-task="%s"><span class="glyph g-%s" aria-hidden="true"></span>'
                        '<span class="stage-task-id">%s</span><span class="stage-task-title">%s</span>'
                        '<span class="stage-task-state">%s</span><span class="stage-task-needs">%s: %s</span></a></li>' % (
                            klass, t['id'], t['id'], klass, t['id'], esc(t['title']), esc(ui['states'].get(t['status'], t['status'])),
                            esc(ui['needs']), need))
        groups.append('<li class="stage-group"><p class="stage-head"><span>%s</span><span>%s</span></p><ol>%s</ol></li>' % (
            esc(ui['stage'].format(n=number + 1)), esc(ui['stage_count'].format(done=done, total=len(listed))), ''.join(rows)))
    return '<ol class="stage-list" aria-label="%s">%s</ol>' % (esc(ui['stage_list']), ''.join(groups))


def load_map_recipe(template_path):
    """Load the architecture-map recipe that sits in recipes/ beside the template's folder."""
    path = Path(template_path).parent / 'recipes' / 'architecture-map.md'
    parts = path.read_text(encoding='utf-8').split('```python\n')
    if len(parts) != 2:
        raise ValueError('the map recipe must hold exactly one fenced python block')
    namespace = {'__name__': 'architecture_map'}
    exec(compile(parts[1].split('\n```')[0] + '\n', str(path), 'exec'), namespace)
    return namespace


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8')), None
    except (OSError, ValueError) as problem:
        return None, '%s: %s' % (path, problem)


def _summary_text(value):
    return value.strip() if isinstance(value, str) else ''


def load_summary(ws):
    """Load only optional narrative fields; canonical plan, board and map data remain authoritative."""
    candidates = (ws / 'view' / 'summary.json', ws / 'summary.json')
    for path in candidates:
        if not path.is_file():
            continue
        data, problem = read_json(path)
        if problem or not isinstance(data, dict):
            return None
        outcomes = []
        raw_outcomes = data.get('outcomes', [])
        if isinstance(raw_outcomes, list):
            for item in raw_outcomes:
                if isinstance(item, dict):
                    title, text = _summary_text(item.get('title')), _summary_text(item.get('text'))
                    if title and text:
                        outcomes.append(dict(title=title, text=text))
        tasks = {}
        raw_tasks = data.get('tasks', {})
        if isinstance(raw_tasks, dict):
            for ident, text in raw_tasks.items():
                if isinstance(ident, str) and re.fullmatch(r'T-\d+', ident) and _summary_text(text):
                    tasks[ident] = _summary_text(text)
        milestones = {}
        raw_milestones = data.get('milestones', {})
        if isinstance(raw_milestones, dict):
            for ident, text in raw_milestones.items():
                if isinstance(ident, str) and _summary_text(text):
                    milestones[ident] = _summary_text(text)
        next_items = [item.strip() for item in data.get('next', []) if isinstance(item, str) and item.strip()] \
            if isinstance(data.get('next', []), list) else []
        owner_items = [item.strip() for item in data.get('you', []) if isinstance(item, str) and item.strip()] \
            if isinstance(data.get('you', []), list) else []
        curated = []
        raw_decisions = data.get('decisions', [])
        if isinstance(raw_decisions, list):
            for item in raw_decisions:
                if not isinstance(item, dict):
                    continue
                text, date = _summary_text(item.get('text')), _summary_text(item.get('date'))
                if text:
                    curated.append(dict(text=text, date=date))
        return dict(title=_summary_text(data.get('title')), kicker=_summary_text(data.get('kicker')),
                    objective=_summary_text(data.get('objective')), outcomes=outcomes, tasks=tasks, milestones=milestones,
                    now=_summary_text(data.get('now')), next=next_items, owner=owner_items, decisions=curated,
                    as_of=_summary_text(data.get('as_of')), board_states=_board_states(data.get('board_states')))
    return None


def _board_states(value):
    """The task states a curated summary was written for, or None when it declares none."""
    if not isinstance(value, dict):
        return None
    return {ident: state for ident, state in value.items() if isinstance(ident, str) and isinstance(state, str)}


def set_aside_stale_prose(summary, export_summary, tasks):
    """Curated status prose describes one board. When it declares that board's task states and the current states
    differ, its time-bound fields are dropped so the canonical counts and records speak alone; prose that declares
    no board is kept as before. Returns the as-of text of the first stale summary, or '' when none is stale."""
    current = {task['id']: task['status'] for task in tasks}
    stale = ''
    if summary is not None and (summary.get('now') or summary.get('next') or summary.get('owner')) \
            and summary.get('board_states') is not None and summary.get('board_states') != current:
        summary.update(now='', next=[], owner=[])
        stale = summary.get('as_of') or '?'
    progress = export_summary.get('progress') if export_summary else None
    if progress and any(progress.get(key) for key in ('achievements', 'open_work', 'dependency', 'next', 'evidence')) \
            and export_summary.get('board_states') is not None and export_summary.get('board_states') != current:
        progress.update(achievements=[], open_work=[], dependency='', next=[], evidence='')
        stale = stale or export_summary.get('as_of') or '?'
    return stale


def _export_pairs(value):
    found = []
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            title, text = _summary_text(item.get('title')), _summary_text(item.get('text'))
            if title and text:
                found.append(dict(title=title, text=text))
    return found


def _export_strings(value):
    return [item.strip() for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


def load_export_summary(ws):
    """Load optional reader-facing export prose; canonical board facts stay outside this file."""
    candidates = (ws / 'view' / 'export-summary.json', ws / 'export-summary.json')
    for path in candidates:
        if not path.is_file():
            continue
        data, problem = read_json(path)
        if problem or not isinstance(data, dict):
            return None
        schema = data.get('schema')
        if schema is not None and (not isinstance(schema, str) or not schema.startswith('executive-presentation')):
            return None
        plan = data.get('plan') if isinstance(data.get('plan'), dict) else {}
        scope = plan.get('scope') if isinstance(plan.get('scope'), dict) else {}
        progress = data.get('progress') if isinstance(data.get('progress'), dict) else {}
        authority = data.get('authority') if isinstance(data.get('authority'), dict) else {}
        return dict(
            title=_summary_text(data.get('title')), kicker=_summary_text(data.get('kicker')),
            context=_summary_text(data.get('context')), purpose=_summary_text(data.get('purpose')),
            combined=_summary_text(data.get('combined')),
            plan=dict(themes=_export_pairs(plan.get('themes')), included=_export_strings(scope.get('included')),
                      deferred=_export_strings(scope.get('deferred')), roadmap=_export_pairs(plan.get('roadmap')),
                      key_choices=_export_pairs(plan.get('key_choices'))),
            progress=dict(meaning=_summary_text(progress.get('meaning')), achievements=_export_pairs(progress.get('achievements')),
                          open_work=_export_pairs(progress.get('open_work')), dependency=_summary_text(progress.get('current_dependency')),
                          next=_export_strings(progress.get('next')), evidence=_summary_text(progress.get('evidence'))),
            as_of=_summary_text(authority.get('as_of')), board_states=_board_states(authority.get('canonical_states')))
    return None


def rel3(rel):
    return (rel[0], rel[1], rel[2] if len(rel) > 2 else '')


def arch_marks(changes):
    marks = {}
    for change in changes:
        mark = marks.setdefault(change['id'], dict(op='change', tasks=[], states=[]))
        if change['op'] == 'add':
            mark['op'] = 'add'
        mark['tasks'].append(change['task'])
        mark['states'].append(change['state'])
    return marks


def arch_badges(cid, marks, stale_ids, ui):
    out = []
    if cid in marks:
        out.append('<span class="abadge %s">%s</span>' % (marks[cid]['op'], esc(ui['a_new'] if marks[cid]['op'] == 'add' else ui['a_change'])))
        out.append('<span class="abadge plain">%s</span>' % esc(', '.join(sorted(set(marks[cid]['tasks'])))))
        out.append('<span class="abadge plain">%s</span>' % esc(ui['a_planned'] if 'planned' in marks[cid]['states'] else ui['a_done']))
    if cid in stale_ids:
        out.append('<span class="abadge old">%s</span>' % esc(ui['a_stale']))
    return ''.join(out)


def arch_attrs(cid, rels, marks, stale_ids):
    related = sorted({b if a == cid else a for a, b, _ in rels if cid in (a, b)})
    relation_types = [dict(**{'from': a, 'to': b, 'label': label}) for a, b, label in rels if cid in (a, b)]
    return 'data-cid="%s" data-rel="%s" data-rel-types="%s"%s%s' % (
        esc(cid), esc(json.dumps(related)), esc(json.dumps(relation_types, ensure_ascii=False, separators=(',', ':'))),
        ' data-change="%s"' % marks[cid]['op'] if cid in marks else '',
        ' data-stale="true"' if cid in stale_ids else '')


def arch_component_kind(comp):
    """Describe the recorded artifact format; do not infer an unrecorded runtime role."""
    sources = comp.get('sources', [])
    title = comp.get('title', '').lower()
    if sources and all('/guides/' in source and source.endswith('.md') for source in sources):
        return 'guide'
    if sources and all('.tmpl.md' in source for source in sources):
        return 'template'
    if sources and all(source.endswith('.md') for source in sources):
        return 'document'
    if sources and all(source.endswith('.py') for source in sources):
        return 'tool'
    if sources and all(source.endswith('.json') for source in sources):
        return 'data'
    if sources and all(source.endswith(('.yml', '.yaml')) for source in sources):
        return 'workflow'
    if sources and all(source.endswith('/') for source in sources):
        return 'package'
    if sources:
        return 'mixed'
    if 'capability' in title or 'capacidad' in title:
        return 'capability'
    if 'page' in title or 'view' in title or 'página' in title or 'vista' in title:
        return 'page'
    return 'component'


def arch_cards(shown, groups, comps, rels, marks, stale_ids, pic, ui):
    out = []
    for index, group in enumerate(groups, 1):
        here = [cid for cid in shown if comps[cid]['group'] == group['id']]
        if not here:
            continue
        cards = []
        for cid in here:
            comp = comps[cid]
            kind = arch_component_kind(comp)
            uses = ['%s → %s' % (esc(label), esc(comps[to]['title'])) for a, to, label in rels if a == cid]
            used = ['%s ← %s' % (esc(label), esc(comps[a]['title'])) for a, to, label in rels if to == cid]
            cards.append(
                '<article class="acard" data-pic="%s" %s data-kind="%s" data-group="%s" tabindex="0" role="button" aria-label="%s">'
                '<p class="component-kicker">%s</p><h5>%s</h5><div class="abadges">%s</div>'
                '<p class="component-role"><span class="visually-hidden">%s: </span>%s</p>'
                '<p class="component-counts"><span>%s <b>%d</b></span><span>%s <b>%d</b></span></p>'
                '<details class="component-source"><summary>%s</summary>%s%s<p class="asrc"><b>%s</b>: %s</p></details></article>' % (
                    pic, arch_attrs(cid, rels, marks if pic == 'after' else {}, stale_ids), kind, esc(group['title']), esc(comp['title']),
                    esc(ui['a_types'][kind]), esc(comp['title']), arch_badges(cid, marks if pic == 'after' else {}, stale_ids, ui),
                    esc(ui['a_role']), esc(comp.get('text', '')),
                    esc(ui['a_in']), len(used), esc(ui['a_out']), len(uses), esc(ui['a_detail']),
                    '<p class="arel"><b>%s</b>: %s</p>' % (esc(ui['a_uses']), '; '.join(uses)) if uses else '',
                    '<p class="arel"><b>%s</b>: %s</p>' % (esc(ui['a_used']), '; '.join(used)) if used else '',
                    esc(ui['a_sources']), ', '.join('<code>%s</code>' % esc(src) for src in comp.get('sources', [])) or '–'))
        out.append('<div class="agroup"><div class="agroup-meta"><span class="agroup-index">%02d</span><h4>%s</h4><span>%s</span></div>'
                   '<div class="acards">%s</div></div>' % (
                       index, esc(group['title']), esc(ui['a_group_count'].format(count=len(here))), ''.join(cards)))
    return ''.join(out)


def label_width(text):
    return 10 + 5.9 * len(text)


def short_label(text, limit=30):
    return text if len(text) <= limit else text[:limit - 1].rstrip() + '…'


def arch_svg(shown, groups, comps, rels, marks, stale_ids, fresh, pic, ui):
    """Boxes in group columns. Every arrow leaves its source from a port of its own, turns on a rail of its own in a
    gutter between columns, or on a lane of its own above the columns when it skips a column, and ends at a port of
    its own: no two arrows share a point or a line, and none passes behind a box. Its words sit beside its source,
    in a lane of the gutter kept free of rails."""
    group_list = [g for g in groups if any(comps[cid]['group'] == g['id'] for cid in shown)]
    columns = [[cid for cid in shown if comps[cid]['group'] == g['id']] for g in group_list]
    count = len(columns)
    node_w, min_h, port_gap, gap_y, head, pad, step = 212, 64, 15, 18, 76, 14, 12
    if not count:
        return '<svg viewBox="0 0 12 12" width="12" height="12" role="group" aria-label="%s"></svg>' % esc(ui['a_diagram'])
    col_of = {cid: k for k, column in enumerate(columns) for cid in column}
    near = {cid: [] for cid in col_of}
    for a, b, _ in rels:
        near[a].append(b)
        near[b].append(a)
    where_rank = {cid: (j + .5) / len(column) for column in columns for j, cid in enumerate(column)}
    for _ in range(4):
        for k, column in enumerate(columns):
            keep = {cid: j for j, cid in enumerate(column)}

            def pull(cid, k=k, keep=keep):
                others = [where_rank[o] for o in near[cid] if col_of[o] != k]
                return (sum(others) / len(others) if others else where_rank[cid], keep[cid])
            column.sort(key=pull)
            for j, cid in enumerate(column):
                where_rank[cid] = (j + .5) / len(column)
    plan = []
    load = [0] * (count + 1)
    for k, (a, b, label) in enumerate(rels):
        ca, cb = col_of[a], col_of[b]
        if ca < cb:
            item = dict(out='R', into='L', ge=ca + 1, gt=cb)
        elif ca > cb:
            item = dict(out='L', into='R', ge=ca, gt=cb + 1)
        else:
            item = dict(out='R', into='R', ge=ca + 1, gt=ca + 1)
        item.update(a=a, b=b, label=label, k=k)
        plan.append(item)
        if item['ge'] == item['gt']:
            load[item['ge']] += 1
        else:
            load[item['ge']] += 1
            load[item['gt']] += 1
    for item in plan:
        if col_of[item['a']] == col_of[item['b']]:
            c = col_of[item['a']]
            side, gutter = ('L', c) if load[c] < load[c + 1] else ('R', c + 1)
            load[item['ge']] -= 1
            load[gutter] += 1
            item.update(out=side, into=side, ge=gutter, gt=gutter)
    for item in plan:
        item['far'] = item['ge'] != item['gt']
    sides = {}
    for item in plan:
        sides.setdefault((item['a'], item['out']), []).append((item['k'], 'from'))
        sides.setdefault((item['b'], item['into']), []).append((item['k'], 'to'))
    height = {cid: max(min_h, (max(len(sides.get((cid, 'L'), [])), len(sides.get((cid, 'R'), []))) + 1) * port_gap) for cid in col_of}
    tall = max(sum(height[cid] for cid in column) + gap_y * (len(column) - 1) for column in columns)
    far = sorted((item for item in plan if item['far']), key=lambda i: (i['ge'], i['gt'], i['k']))
    channel = (len(far) + 1) * step + 6 if far else 0
    top = {}
    for column in columns:
        y = channel + head + pad
        for cid in column:
            top[cid] = y
            y += height[cid] + gap_y
    by_k = {item['k']: item for item in plan}

    def other_end(k, role):
        item = by_k[k]
        if item['far']:
            return -1e6
        cid = item['b'] if role == 'from' else item['a']
        return top[cid] + height[cid] / 2

    slot = {}
    for (cid, side), listed in sides.items():
        ordered = sorted(listed, key=lambda u: (other_end(*u), u[0], u[1]))
        for n, key in enumerate(ordered):
            slot[key] = top[cid] + (n + 1) * height[cid] / (len(ordered) + 1)
    stubs = {}
    for item in plan:
        stubs.setdefault(item['ge'], []).append((item['k'], 'from', item['a']))
        stubs.setdefault(item['gt'], []).append((item['k'], 'to', item['b']))
    for listed in stubs.values():
        previous = None
        for k, role, cid in sorted(listed, key=lambda u: (slot[(u[0], u[1])], u[0], u[1])):
            if previous is not None and slot[(k, role)] < previous + 3:
                slot[(k, role)] = min(previous + 3, top[cid] + height[cid] - 2)
            previous = slot[(k, role)]
    lane_left, lane_right = [0] * (count + 1), [0] * (count + 1)
    for item in plan:
        words = label_width(short_label(item['label']))
        if item['out'] == 'R':
            lane_left[item['ge']] = max(lane_left[item['ge']], words)
        else:
            lane_right[item['ge']] = max(lane_right[item['ge']], words)
    rails = {}
    for item in plan:
        rails.setdefault(item['ge'], []).append((item['k'], 'ge'))
        if item['far']:
            rails.setdefault(item['gt'], []).append((item['k'], 'gt'))
    rail_w = [max(28 if 0 < g < count else 12, (len(rails.get(g, [])) + 1) * step) for g in range(count + 1)]
    gutter_w = [lane_left[g] + rail_w[g] + lane_right[g] for g in range(count + 1)]
    gutter_x = []
    x = 6
    for g in range(count + 1):
        gutter_x.append(x)
        x += gutter_w[g] + (node_w + 2 * pad if g < count else 0)
    total_w = x + 6
    total_h = channel + head + pad + tall + pad
    left_x = {cid: gutter_x[col_of[cid]] + gutter_w[col_of[cid]] + pad for cid in col_of}

    def stub_side(item, which):
        """Which side of the gutter a rail's horizontal part touches, and at what height."""
        if which == 'ge':
            return ('left' if item['out'] == 'R' else 'right'), slot[(item['k'], 'from')]
        return ('left' if item['into'] == 'R' else 'right'), slot[(item['k'], 'to')]

    rail_x = {}
    for g, listed in rails.items():
        loops_left, loops_right, ups, downs = [], [], [], []
        for k, which in listed:
            item = by_k[k]
            if not item['far']:
                y1, y2 = slot[(k, 'from')], slot[(k, 'to')]
                if item['out'] == item['into']:
                    (loops_left if item['out'] == 'R' else loops_right).append((abs(y2 - y1), k, which))
                    continue
                y_left, y_right = (y1, y2) if item['out'] == 'R' else (y2, y1)
            else:
                side, y = stub_side(item, which)
                y_left, y_right = (y, -1e6) if side == 'left' else (-1e6, y)
            (downs if y_right > y_left else ups).append(((y_left, y_right), k, which))
        ordered = [(k, w) for _, k, w in sorted(loops_left)]
        ordered += [(k, w) for _, k, w in sorted(ups, key=lambda u: (u[0][0], u[0][1], u[1]))]
        ordered += [(k, w) for _, k, w in sorted(downs, key=lambda u: (-u[0][0], -u[0][1], u[1]))]
        ordered += [(k, w) for _, k, w in sorted(loops_right, reverse=True)]
        start = gutter_x[g] + lane_left[g]
        for n, key in enumerate(ordered):
            rail_x[key] = start + (n + 1) * rail_w[g] / (len(ordered) + 1)
    lane = {item['k']: channel - (n + 1) * step for n, item in enumerate(far)}
    out = ['<svg viewBox="0 0 %d %d" width="%d" height="%d" role="group" aria-label="%s"><defs><marker id="arrow-%s" viewBox="0 0 8 8" refX="7.4" refY="4" '
           'markerWidth="7" markerHeight="7" orient="auto"><path class="arrowhead" d="M 0 0.6 L 8 4 L 0 7.4 z"/></marker>'
           '<marker id="arrow-on-%s" viewBox="0 0 8 8" refX="7.4" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path class="arrowhead-on" d="M 0 0.6 L 8 4 L 0 7.4 z"/></marker></defs>' % (
               total_w, total_h, total_w, total_h, esc(ui['a_diagram']), pic, pic)]
    for k, column in enumerate(columns):
        group = group_list[k]
        band_x = gutter_x[k] + gutter_w[k]
        out.append('<rect class="band" data-band="%d" x="%.1f" y="%d" width="%d" height="%d"><title>%s</title></rect>' % (
            k % 4, band_x, channel, node_w + 2 * pad, total_h - channel, esc(group['title'])))
        group_title = ''.join('<tspan x="%.1f" dy="%d">%s</tspan>' % (band_x + pad, 0 if index == 0 else 18, esc(line))
                              for index, line in enumerate(wrap(group['title'], 26, 2)))
        out.append('<text class="agroup-head" x="%.1f" y="%d">%s</text><text class="agroup-count" x="%.1f" y="%d">%s</text>' % (
            band_x + pad, channel + 28, group_title, band_x + pad, channel + 66, esc(ui['a_group_count'].format(count=len(column)))))
    labels = []
    for item in plan:
        a, b, k = item['a'], item['b'], item['k']
        start = (left_x[a] + (node_w if item['out'] == 'R' else 0), slot[(k, 'from')])
        end = (left_x[b] + (node_w if item['into'] == 'R' else 0), slot[(k, 'to')])
        if item['far']:
            points = [start, (rail_x[(k, 'ge')], start[1]), (rail_x[(k, 'ge')], lane[k]), (rail_x[(k, 'gt')], lane[k]),
                      (rail_x[(k, 'gt')], end[1]), end]
        else:
            points = [start, (rail_x[(k, 'ge')], start[1]), (rail_x[(k, 'ge')], end[1]), end]
        path = 'M%.1f %.1f' % points[0] + ''.join(' L%.1f %.1f' % p for p, q in zip(points[1:], points) if p != q)
        out.append('<path class="aedge%s" data-from="%s" data-to="%s" d="%s" marker-end="url(#arrow-%s)"><title>%s</title></path>' % (
            ' new' if (a, b, item['label']) in fresh else '', esc(a), esc(b), path, pic,
            esc('%s → %s: %s' % (comps[a]['title'], comps[b]['title'], item['label']))))
        if item['out'] == 'R':
            spot = (start[0] + 7, start[1] - 4, 'start')
        else:
            spot = (start[0] - 7, start[1] - 4, 'end')
        labels.append('<text class="aelabel" data-from="%s" data-to="%s" x="%.1f" y="%.1f" text-anchor="%s">%s</text>' % (
            esc(a), esc(b), spot[0], spot[1], spot[2], esc(short_label(item['label']))))
    for cid in shown:
        x, y, h = left_x[cid], top[cid], height[cid]
        comp = comps[cid]
        kind = arch_component_kind(comp)
        lines = wrap(comp['title'], 24, 2)
        text = ''.join('<tspan x="%.1f" dy="%d">%s</tspan>' % (x + 14, 0 if k == 0 else 17, esc(line)) for k, line in enumerate(lines))
        tag = ''
        if cid in stale_ids:
            tag = ui['a_stale']
        elif pic == 'after' and cid in marks:
            tag = ui['a_new'] if marks[cid]['op'] == 'add' else ui['a_change']
        caption = '%s. %s. %s' % (comp['title'], ui['a_types'][kind], comp.get('text', ''))
        badge = ''
        if tag:
            tag_w = 12 + 6.4 * len(tag)
            badge = '<g class="anode-tag"><rect x="%.1f" y="%.1f" width="%.1f" height="16"/><text x="%.1f" y="%.1f">%s</text></g>' % (
                x + node_w - tag_w, y, tag_w, x + node_w - tag_w / 2, y + 11.5, esc(tag.upper()))
        out.append('<g class="anode" %s data-kind="%s" tabindex="0" role="button" aria-label="%s"><title>%s</title>'
                   '<rect x="%.1f" y="%.1f" width="%d" height="%d"/>%s'
                   '<text class="component-kicker" x="%.1f" y="%.1f">%s</text><text class="component-note ant" x="%.1f" y="%.1f">%s</text></g>' % (
                       arch_attrs(cid, rels, marks if pic == 'after' else {}, stale_ids), kind, esc(caption), esc(caption),
                       x, y, node_w, h, badge, x + 14, y + 22, esc(ui['a_types'][kind].upper()), x + 14, y + 42, text))
    out += labels
    out.append('</svg>')
    return ''.join(out)


def arch_relation_guide(rels, comps, ui):
    rows = []
    for source, target, label in rels:
        rows.append('<li class="arel-row" data-from="%s" data-to="%s"><span class="arel-from">%s</span> '
                    '<span class="arel-label">%s</span> <span class="arel-arrow" aria-hidden="true">→</span> '
                    '<span class="arel-to">%s</span></li>' % (
                        esc(source), esc(target), esc(comps[source].get('title') or source), esc(label),
                        esc(comps[target].get('title') or target)))
    summary = ui['a_rel_all'].format(count=len(rels))
    return ('<div class="arel-guide"><h4 class="arel-heading">%s</h4><p class="arel-hint">%s</p>'
            '<p class="arel-summary" data-all="%s" data-focus="%s" aria-live="polite">%s</p>'
            '<ul class="arel-list" tabindex="0" aria-label="%s">%s</ul>%s</div>') % (
                esc(ui['a_rel_heading']), esc(ui['a_rel_hint']), esc(summary), esc(ui['a_rel_focus']),
                esc(summary), esc(ui['a_rel_list']), ''.join(rows),
                '<p class="arel-empty">%s</p>' % esc(ui['a_rel_empty']) if not rows else '')


def arch_section(mapm, base, delta, scope, root, ui):
    """The Before and after section, and the island's map object. Assumes the delta passed validate."""
    later = mapm['after'](base, delta)
    changes = delta.get('changes', [])
    changed = sorted({c['id'] for c in changes})
    base_ids = sorted(c['id'] for c in base['components'])
    after_ids = sorted(c['id'] for c in later['components'])
    if scope == 'changed':
        after_ids = [i for i in mapm['neighbors'](later, changed) if i in set(after_ids)]
        today_ids = [i for i in after_ids if i in set(base_ids)]
    else:
        today_ids = base_ids
    stale_ids = set(mapm['stale'](base, root)) & set(today_ids)
    island = dict(today=today_ids, after=after_ids, changed=changed, stale=sorted(stale_ids))
    head = '<header class="sec-head"><h2>%s</h2><p class="sec-lede">%s</p></header>' % (esc(ui['a_title']), esc(ui['a_note']))
    if scope == 'changed' and not changes:
        return '<section class="sec" id="architecture" data-map="shown">%s<p class="anote">%s</p></section>' % (head, esc(ui['a_nochange'])), island
    marks = arch_marks(changes)
    fresh = {rel3(r) for c in changes for r in c.get('relations', [])}
    groups = base['groups']
    pictures = [('today', base, today_ids)] + ([('after', later, after_ids)] if changes else [])
    parts = []
    for pic, source, shown in pictures:
        comps = {c['id']: c for c in source['components']}
        shown_set = set(shown)
        rels = [rel3(r) for r in source.get('relations', []) if r[0] in shown_set and r[1] in shown_set]
        parts.append(
            '<div class="arch-pic" data-pic="%s"><div class="arch-pic-head"><h3>%s</h3><span>%s</span></div>'
            '<div class="apanel" data-view="cards">%s</div>'
            '<div class="apanel" data-view="diagram"><div class="canvas-bar"><p>%s</p><div class="zoom" role="group" aria-label="%s">'
            '<button type="button" class="tool" data-zoom="out" aria-label="%s">−</button><output class="zoom-level">100%%</output>'
            '<button type="button" class="tool" data-zoom="in" aria-label="%s">+</button><button type="button" class="tool" data-zoom="fit">%s</button></div></div>'
            '<div class="ascroll canvas" tabindex="0" role="region" aria-label="%s">%s</div></div>%s</div>' % (
                pic, esc(ui['a_today'] if pic == 'today' else ui['a_after']), esc(ui['a_rel_all'].format(count=len(rels))),
                arch_cards(shown, groups, comps, rels, marks, stale_ids, pic, ui),
                esc(ui['a_diagram_help']), esc(ui['zoom']), esc(ui['zoom_out']), esc(ui['zoom_in']), esc(ui['fit']),
                esc(ui['a_diagram']), arch_svg(shown, groups, comps, rels, marks, stale_ids, fresh, pic, ui),
                arch_relation_guide(rels, comps, ui)))
    tabs = ('<div class="atabs segmented" role="tablist" aria-label="%s"><button type="button" role="tab" class="seg" data-view="cards" aria-selected="true">%s</button>'
            '<button type="button" role="tab" class="seg" data-view="diagram" aria-selected="false">%s</button></div>') % (
               esc(ui['a_views']), esc(ui['a_cards']), esc(ui['a_diagram']))
    switch = ''
    if changes:
        switch = ('<div class="apics segmented" role="radiogroup" aria-label="%s"><button type="button" role="radio" class="seg" data-pic="today" aria-checked="false">%s</button>'
                  '<button type="button" role="radio" class="seg" data-pic="after" aria-checked="true">%s</button></div>') % (
                     esc(ui['a_pics']), esc(ui['a_today']), esc(ui['a_after']))
    added = sorted({c['id'] for c in changes if c['op'] == 'add'})
    edited = sorted({c['id'] for c in changes if c['op'] != 'add'} - set(added))
    later_comps = {c['id']: c for c in later['components']}
    change_rows = ''.join(
        '<li><span class="abadge %s">%s</span><span class="change-title">%s</span><span class="change-tasks">%s</span></li>' % (
            'add' if cid in added else 'change', esc(ui['a_new'] if cid in added else ui['a_change']), esc(later_comps[cid]['title']),
            esc(', '.join(sorted({c['task'] for c in changes if c['id'] == cid}))))
        for cid in added + edited if cid in later_comps)
    figures = ('<dl class="arch-figures"><div><dt>%s</dt><dd>%d</dd></div><div><dt>%s</dt><dd>%d</dd></div>'
               '<div><dt>%s</dt><dd>%d</dd></div><div><dt>%s</dt><dd>%d</dd></div></dl>') % (
                   esc(ui['a_count']), len(after_ids), esc(ui['a_changes']), len(changes), esc(ui['a_new']), len(added),
                   esc(ui['a_change']), len(edited))
    notes = [ui['a_whole'] if scope == 'all' else ui['a_changed_only']]
    if not changes:
        notes.append(ui['a_nochange'])
    want, have = delta.get('base_revision'), base.get('verified_at', {}).get('revision')
    if want and have and want != have:
        notes.append(ui['a_mismatch'].format(have=have, want=want))
    project = '<div class="arch-project"><h3>%s</h3><p>%s</p></div>' % (esc(base.get('project', '')), esc(base.get('summary', '')))
    changes_html = ('<div class="arch-changes"><h3>%s</h3><ul>%s</ul></div>' % (esc(ui['a_changes_title']), change_rows)) if change_rows else ''
    legend = ('<ul class="arch-legend" aria-label="%s"><li><i class="legend-mark new" aria-hidden="true"></i>%s</li>'
              '<li><i class="legend-mark change" aria-hidden="true"></i>%s</li><li><i class="legend-mark old" aria-hidden="true"></i>%s</li></ul>') % (
                  esc(ui['architecture_legend']), esc(ui['a_new']), esc(ui['a_change']), esc(ui['a_stale']))
    html_out = ('<section class="sec" id="architecture" data-map="shown">%s<div class="arch-intro">%s%s%s</div>'
                '<div class="arch-bar">%s%s%s</div><p class="anote">%s</p>%s'
                '<aside class="lens" id="architecture-lens" aria-label="%s" data-in="%s" data-out="%s" data-none="%s" hidden>'
                '<header class="lens-head"><p class="lens-kicker">%s</p><button type="button" class="tool lens-close">%s</button></header>'
                '<div class="lens-body" aria-live="polite"></div><p class="lens-hint">%s</p></aside></section>') % (
        head, project, figures, changes_html, switch, tabs, legend, esc(' '.join(notes)), ''.join(parts),
        esc(ui['a_lens']), esc(ui['a_in']), esc(ui['a_out']), esc(ui['a_lens_none']), esc(ui['a_lens']), esc(ui['close']), esc(ui['a_lens_hint']))
    return html_out, island


def arch_none(ui):
    return '<section class="sec" id="architecture" data-map="none"><header class="sec-head"><h2>%s</h2><p class="sec-lede">%s</p></header></section>' % (
        esc(ui['a_title']), esc(ui['a_none']))


def title_block(tasks, reqs, cover, decisions, working, fields, focused, stamp, method, ui):
    """The hero's title block: the progress figure, a strip with one cell per task and the plan's vital counts."""
    cells = []
    if focused:
        figure = '<p class="tb-figure"><b>%d</b><span>%s</span></p>' % (len(reqs), esc(ui['st_reqs']))
        state = fields.get('state', '')
        strip = '<p class="tb-note">%s</p>' % esc(ui['summary_focused'].format(reqs=len(reqs)))
        if state:
            strip += '<p class="tb-state"><span class="tb-k">%s</span> %s</p>' % (esc(ui['state']), esc(state))
        cells = [(ui['st_checks'], str(sum(1 for v in reqs.values() if v[1]))), (ui['st_dec'], str(len(decisions))),
                 (ui['st_open'], str(len(working)))]
    else:
        done = sum(1 for t in tasks if t['status'] == 'Complete')
        figure = '<p class="tb-figure"><b>%d</b><span class="tb-of">/%d</span><span>%s</span></p>' % (done, len(tasks), esc(ui['tb_tasks']))
        marks = ''.join('<a class="tb-cell s-%s" href="#task-%s" data-task="%s" title="%s"><span class="visually-hidden">%s</span></a>' % (
            STATE_CLASS.get(t['status'], 'draft'), t['id'], t['id'],
            esc('%s · %s · %s' % (t['id'], t['title'], ui['states'].get(t['status'], t['status']))),
            esc('%s %s' % (t['id'], ui['states'].get(t['status'], t['status'])))) for t in tasks)
        counts = {}
        for t in tasks:
            counts[t['status']] = counts.get(t['status'], 0) + 1
        states = ''.join('<li><span class="glyph g-%s" aria-hidden="true"></span>%s <b>%d</b></li>' % (
            STATE_CLASS.get(s, 'draft'), esc(ui['states'].get(s, s)), counts[s]) for s in DEFAULT_STATES + sorted(set(counts) - set(DEFAULT_STATES)) if s in counts)
        strip = '<div class="tb-strip" role="list" aria-label="%s" style="--cells:%d">%s</div><ul class="tb-states">%s</ul>' % (
            esc(ui['tb_strip']), max(1, min(len(tasks), 24)), marks.replace('<a class="tb-cell', '<a role="listitem" class="tb-cell'), states)
        covered = sum(1 for r in cover if cover[r])
        cells = [(ui['st_cov'], '%d / %d' % (covered, len(reqs))), (ui['st_dec'], str(len(decisions))), (ui['st_open'], str(len(working)))]
    cells.append((ui['built'], stamp))
    grid = ''.join('<div class="tb-cell-k"><dt>%s</dt><dd>%s</dd></div>' % (esc(k), esc(v)) for k, v in cells)
    return ('<aside class="title-block" aria-label="%s"><p class="tb-label">%s</p>%s%s<dl class="tb-grid">%s</dl>'
            '<p class="tb-method">%s</p></aside>') % (esc(ui['progress']), esc(ui['progress']), figure, strip, grid, esc(method))


def status_section(summary, export_summary, fields, tasks, focused, snapshot, working_html, title, plan, ui, stale_prose=''):
    """Where the plan stands: the current narrative, what needs the owner, what is done and open, and the raw snapshot."""
    counts = {}
    for task in tasks:
        counts[task['status']] = counts.get(task['status'], 0) + 1
    done, total = counts.get('Complete', 0), len(tasks)
    if tasks:
        headline = ui['mission_complete'].format(done=done, total=total)
        if total - done:
            headline += ' ' + ui['mission_remaining'].format(count=total - done)
    else:
        headline = ui['mission_no_board']
    progress = export_summary.get('progress', {}) if export_summary else {}
    achievements, open_work = progress.get('achievements', []), progress.get('open_work', [])
    next_steps = progress.get('next', []) or (summary['next'] if summary and summary.get('next') else [])
    lead = []
    if stale_prose:
        lead.append('<p class="status-stale" role="note">%s</p>' % esc(ui['stale_prose'].format(as_of=stale_prose)))
    if summary and summary.get('now'):
        lead.append('<p class="status-now"><span class="status-k">%s</span>%s</p>' % (esc(ui['now']), esc(summary['now'])))
    if summary and summary.get('owner'):
        lead.append('<div class="status-you"><h3>%s</h3><ul>%s</ul></div>' % (
            esc(ui['owner']), ''.join('<li>%s</li>' % esc(item) for item in summary['owner'])))
    blocks = []
    if achievements:
        blocks.append('<div class="status-block"><h3>%s</h3><ul class="status-list">%s</ul></div>' % (
            esc(ui['mission_achievements']), ''.join('<li><b>%s</b><span>%s</span></li>' % (esc(i['title']), esc(i['text'])) for i in achievements)))
    if open_work:
        blocks.append('<div class="status-block is-open"><h3>%s</h3><ul class="status-list">%s</ul></div>' % (
            esc(ui['mission_open_work']), ''.join('<li><b>%s</b><span>%s</span></li>' % (esc(i['title']), esc(i['text'])) for i in open_work)))
    if next_steps:
        blocks.append('<div class="status-block"><h3>%s</h3><ol class="status-steps">%s</ol></div>' % (
            esc(ui['mission_next']), ''.join('<li>%s</li>' % esc(item) for item in next_steps)))
    raw = snapshot or fields.get('state', '') or ui['snapshot_none']
    purpose = (summary.get('objective') if summary else '') or objective_of(plan)
    raw_details = ('<details class="snapshot-source"><summary>%s</summary><p class="mission-purpose"><b>%s</b>: %s</p>'
                   '<pre class="snap">%s</pre></details>') % (esc(ui['mission_raw_snapshot']), esc(ui['mission_purpose']), esc(purpose), esc(raw))
    return ('<section class="sec status" id="snapshot"><header class="sec-head"><h2>%s</h2><p class="status-headline">%s</p></header>'
            '<div class="status-grid"><div class="status-lead">%s%s</div><div class="status-blocks">%s</div></div>%s</section>') % (
        esc(ui['snapshot']), esc(headline), ''.join(lead), working_html, ''.join(blocks), raw_details)


def task_list(tasks, cover, down, live, summary, ui, counts, present):
    bar = '<button type="button" class="chip" data-filter="all" aria-pressed="true">%s <b>%d</b></button>' % (esc(ui['all']), len(tasks))
    bar += ''.join('<button type="button" class="chip" data-filter="%s" aria-pressed="false"><span class="glyph g-%s" aria-hidden="true"></span>%s <b>%d</b></button>' % (
        esc(s), STATE_CLASS.get(s, 'draft'), esc(ui['states'].get(s, s)), counts[s]) for s in present)
    cards = []
    for t in tasks:
        klass = STATE_CLASS.get(t['status'], 'draft')
        traced = [r for r in cover if t['id'] in cover[r]]
        chips = lambda ids, prefix: ''.join('<a class="ref" href="#%s%s">%s</a>' % (prefix, esc(i), esc(i)) for i in ids) or '<span class="none">%s</span>' % esc(ui['nothing'])
        purpose = summary['tasks'].get(t['id'], '') if summary else ''
        cards.append(
            '<article class="task s-%s" id="task-%s" data-status="%s" data-upstream="%s" data-downstream="%s"%s>'
            '<button type="button" class="task-head" aria-expanded="false" aria-controls="detail-%s">'
            '<span class="task-id">%s</span><span class="pill"><span class="glyph g-%s" aria-hidden="true"></span>%s</span>%s'
            '<span class="task-title">%s</span>%s<span class="task-links">%s %d · %s %d</span></button>'
            '<div class="detail" id="detail-%s"><dl class="task-facts"><div><dt>%s</dt><dd>%s</dd></div><div><dt>%s</dt><dd>%s</dd></div>'
            '<div><dt>%s</dt><dd>%s</dd></div><div><dt>%s</dt><dd><code>%s</code></dd></div></dl>'
            '<p class="task-actions"><button type="button" class="tool" data-trace="up">%s</button><button type="button" class="tool" data-trace="down">%s</button></p></div></article>' % (
                klass, t['id'], esc(t['status']), ' '.join(sorted(t['deps'])), ' '.join(sorted(down[t['id']])),
                ' data-live="true"' if t['id'] in live else '', t['id'], t['id'], klass,
                esc(ui['states'].get(t['status'], t['status'])), ' <span class="live">%s</span>' % esc(ui['live']) if t['id'] in live else '',
                esc(t['title']), '<span class="task-purpose">%s</span>' % esc(purpose) if purpose else '',
                esc(ui['needs']), len(t['deps']), esc(ui['unblocks']), len(down[t['id']]), t['id'],
                esc(ui['needs']), chips(sorted(t['deps']), 'task-'), esc(ui['unblocks']), chips(sorted(down[t['id']]), 'task-'),
                esc(ui['requirements']), chips(traced, 'requirement-'), esc(ui['brief']), esc(t['brief']),
                esc(ui['trace_up']), esc(ui['trace_down'])))
    return ('<section class="sec" id="tasks"><header class="sec-head"><h2>%s</h2><p class="sec-lede">%s</p></header>'
            '<div class="bar" role="toolbar" aria-label="%s">%s</div><div class="tasks">%s</div>'
            '<p class="empty-filter" hidden>%s</p></section>') % (
        esc(ui['tasks']), esc(ui['tasks_lede']), esc(ui['filter']), bar, ''.join(cards), esc(ui['filter_empty']))


def export_section(export_ui):
    cards = ''.join('<button type="button" class="scope-card" data-scope="%s" aria-pressed="%s" tabindex="-1"><span class="scope-sheet" aria-hidden="true"><i></i><i></i><i></i></span>'
                    '<span class="scope-name">%s</span><span class="scope-text">%s</span></button>' % (
                        value, 'true' if value == 'both' else 'false', esc(export_ui[name]), esc(export_ui[name + '_desc']))
                    for value, name in (('plan', 'plan'), ('progress', 'progress'), ('both', 'both')))
    return ('<section class="sec export" id="export"><header class="sec-head"><h2>%s</h2><p class="sec-lede">%s</p></header>'
            '<div class="scope-cards" aria-hidden="true">%s</div>'
            '<div class="export-controls"><label for="plan-export-scope">%s</label>'
            '<select id="plan-export-scope" aria-label="%s"><option value="plan">%s</option>'
            '<option value="progress">%s</option><option value="both" selected>%s</option></select>'
            '<button type="button" class="action" id="plan-export-button">%s</button><p class="export-hint">%s</p>'
            '<p id="plan-export-status" role="status" aria-live="polite" data-error="%s"></p></div></section>') % (
        esc(export_ui['export_title']), esc(export_ui['export_lede']), cards, esc(export_ui['scope']), esc(export_ui['scope']),
        esc(export_ui['plan']), esc(export_ui['progress']), esc(export_ui['both']), esc(export_ui['print']), esc(export_ui['save_pdf']),
        esc(export_ui['print_error']))


def fill(template, values):
    missing = sorted(set(re.findall(r'\{\{(\w+)\}\}', template)) - set(values))
    if missing:
        raise KeyError(', '.join(missing))
    return re.sub(r'\{\{(\w+)\}\}', lambda m: values[m.group(1)], template)


def main():
    parser = argparse.ArgumentParser(description='Write the plan view of a workspace.')
    parser.add_argument('--template', required=True)
    parser.add_argument('--map', dest='map_base', help='the project map (tackle-map/1) to draw before and after the plan')
    parser.add_argument('--map-scope', choices=('all', 'changed'), default='all',
                        help='draw the whole map, or only the changed components with their neighbors')
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
    export_ui = EXPORT_UI[lang]
    reqs, fields = parse_requirements(plan)
    requirement_rows = parse_requirement_rows(plan, reqs)
    summary = load_summary(ws)
    export_summary = load_export_summary(ws)
    if focused and not reqs:
        problems.append('the Focused plan names no requirement id in its Purpose / requirements line or its criteria table')
    tasks, states, board = [], DEFAULT_STATES, ''
    stale_prose = ''
    if not focused:
        board = read(ws, 'task-board.md')
        if not board:
            problems.append('task-board.md is missing or empty')
        states, tasks = parse_board(board, problems)
        if board and not tasks:
            problems.append('the board has no task rows')
        stale_prose = set_aside_stale_prose(summary, export_summary, tasks)
        progress = export_summary.get('progress', {}) if export_summary else {}
        for name, data, prose in (
                ('the curated summary', summary, summary and (summary.get('now') or summary.get('next') or summary.get('owner'))),
                ('the executive summary', export_summary,
                 any(progress.get(key) for key in ('achievements', 'open_work', 'dependency', 'next', 'evidence')))):
            if data is not None and prose and data.get('board_states') is None:
                print('note: %s declares no board states, so its status prose cannot be checked for staleness'
                      % name, file=sys.stderr)
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
    arch, missing_base = None, False
    if args.map_base:
        try:
            mapm = load_map_recipe(args.template)
        except (OSError, ValueError, SyntaxError) as problem:
            print('cannot load the architecture map recipe: %s' % problem, file=sys.stderr)
            return 2
        base, trouble = (None, None) if not Path(args.map_base).exists() else read_json(args.map_base)
        if not Path(args.map_base).exists():
            missing_base = True
        elif trouble:
            problems.append('cannot read the base map %s' % trouble)
        elif not isinstance(base, dict) or base.get('schema') != 'tackle-map/1':
            problems.append('the base map is not schema tackle-map/1')
            base = None
        delta = dict(schema='tackle-map-delta/1', changes=[])
        if (ws / 'map-delta.json').is_file() and not missing_base:
            delta, trouble = read_json(ws / 'map-delta.json')
            if trouble:
                problems.append('cannot read the map delta %s' % trouble)
        if base is not None and not any(p.startswith('cannot read the map delta') for p in problems):
            problems += ['map: ' + line for line in mapm['validate'](base, delta)]
        arch = (base, delta, mapm) if base is not None else None
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
    map_html, map_island = '', None
    if arch:
        above = Path(os.path.abspath(ws)).parents
        root = above[2] if len(above) > 2 else above[-1]
        map_html, map_island = arch_section(arch[2], arch[0], arch[1], args.map_scope, root, ui)
    elif missing_base or (ws / 'map-delta.json').is_file():
        map_html = arch_none(ui)
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
    presentation_title = (summary.get('title') if summary else '') or title
    presentation_kicker = (summary.get('kicker') if summary else '') or kicker
    presentation_objective = (summary.get('objective') if summary else '') or objective_of(plan)
    method = 'Tackle ' + version.group(1) if version else export_ui['methodology_unavailable']

    def scope_label(scope):
        return ui['plan_scope'] if scope == 'PLAN' else ui['run_scope'] if scope == 'RUN' else scope

    if working:
        items = ''.join('<li data-working-scope="%s"><span class="pulse" aria-hidden="true"></span>%s · %s</li>' % (
            esc(w['scope']), esc(scope_label(w['scope'])), esc(ui['roles'].get(w['role'], w['role']))) for w in working)
        working_html = '<div id="working-now" class="working"><h3>%s</h3><ul>%s</ul></div>' % (esc(ui['working']), items)
    else:
        working_html = '<div id="working-now" class="working is-idle"><h3>%s</h3><p data-working="none">%s</p></div>' % (
            esc(ui['working']), esc(ui['working_none']))

    covered = sum(1 for r in cover if cover[r])
    if focused:
        graph_html = ('<section class="sec flow" id="graph"><header class="sec-head"><h2>%s</h2><p class="sec-lede">%s</p></header></section>' % (
            esc(ui['graph']), esc(ui['graph_none'])))
        tasks_html = ''
    else:
        counts = {}
        for t in tasks:
            counts[t['status']] = counts.get(t['status'], 0) + 1
        present = [s for s in states if s in counts]
        edges = reduce_edges(ids, {t['id']: t['deps'] for t in tasks})
        layout = choose_layout(ids, stage, edges)
        legend = ''.join('<li><span class="glyph g-%s" aria-hidden="true"></span>%s</li>' % (
            STATE_CLASS.get(s, 'draft'), esc(ui['states'].get(s, s))) for s in present)
        legend += '<li><span class="line-mark met" aria-hidden="true"></span>%s</li><li><span class="line-mark open" aria-hidden="true"></span>%s</li>' % (
            esc(ui['legend_met']), esc(ui['legend_open']))
        graph_html = (
            '<section class="sec flow" id="graph"><header class="sec-head"><h2>%s</h2><p class="sec-lede">%s</p></header>'
            '<div class="canvas-bar"><ul class="legend" aria-label="%s">%s</ul><div class="canvas-tools">'
            '<button type="button" class="tool" id="clear-trace" hidden>%s</button><div class="zoom" role="group" aria-label="%s">'
            '<button type="button" class="tool" data-zoom="out" aria-label="%s">−</button><output class="zoom-level">100%%</output>'
            '<button type="button" class="tool" data-zoom="in" aria-label="%s">+</button><button type="button" class="tool" data-zoom="fit">%s</button></div></div></div>'
            '<div class="flow-stage"><div class="map"><div class="gscroll canvas" tabindex="0" role="region" aria-label="%s">%s</div></div>'
            '<aside class="inspector" id="flow-inspector" aria-live="polite" data-open="%s"><p class="inspector-empty">%s</p><div class="inspector-body" hidden></div></aside></div>'
            '<button type="button" class="tool flow-toggle" aria-expanded="false" data-show="%s" data-hide="%s" hidden>%s</button>'
            '%s<p class="flow-note">%s %s</p></section>') % (
            esc(ui['graph']), esc(ui['graph_note']), esc(ui['legend']), legend, esc(ui['clear']), esc(ui['zoom']), esc(ui['zoom_out']),
            esc(ui['zoom_in']), esc(ui['fit']), esc(ui['graph']), graph_svg(tasks, layout, live, ui), esc(ui['inspector_open']), esc(ui['inspector_empty']),
            esc(ui['show_diagram']), esc(ui['hide_diagram']), esc(ui['show_diagram']),
            stage_list(tasks, layout[0], edges, ui), esc(ui['graph_reduced']), esc(ui['stage_note']))
        tasks_html = task_list(tasks, cover, down, live, summary, ui, counts, present)
    overview_html = presentation_overview(summary, objective_of(plan), ui)
    status_html = status_section(summary, export_summary, fields, tasks, focused, snapshot, working_html, title, plan, ui, stale_prose)
    nav = [('snapshot', ui['n_now'])]
    if overview_html:
        nav.append(('overview', ui['n_overview']))
    if not focused:
        nav += [('graph', ui['n_graph']), ('tasks', ui['n_tasks'])]
    if map_html:
        nav.append(('architecture', ui['n_arch']))
    nav += [('requirements', ui['n_requirements']), ('decisions', ui['n_decisions']), ('export', ui['n_export'])]
    technical = requirements_section(requirement_rows, cover, focused, ui) + decisions_section(summary, decisions, ui) + \
        '<section class="sec technical" id="technical"><h2 class="visually-hidden">%s</h2>%s</section>' % (
            esc(ui['technical_title']), technical_details(reqs, cover, fields, tasks, decisions, focused, ui))
    footer = '<p>%s%s · <a href="%s" target="_blank" rel="noopener noreferrer">%s</a></p><p>%s %s</p>' % (
        esc(ui['made_with']), ' ' + version.group(1) if version else '', REPO_URL, REPO_URL.split('//', 1)[1], esc(ui['built']), esc(stamp))
    island = json.dumps(dict(
        schema='tackle-plan-view/1', focused=focused, language=lang, built=stamp,
        tasks=[dict(id=t['id'], status=t['status'], deps=t['deps'], title=t['title'], brief=t['brief'], traces=t['traces']) for t in tasks],
        requirements={r: cover[r] for r in cover}, decisions=[d['id'] for d in decisions], snapshot=snapshot, working=working,
        map=map_island),
        ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    print_reports = printable_reports(plan, focused, fields, reqs, requirement_rows, decisions, summary, export_summary, tasks, working, board, snapshot,
                                      stamp, method, title, ui, export_ui)
    values = dict(
        lang=lang, title=esc(presentation_title), brand=esc(presentation_title if len(presentation_title) <= 40 else presentation_title[:39] + '…'),
        kicker=esc(presentation_kicker), title_size='long' if len(presentation_title) > 28 else 'short',
        objective='<p class="objective">%s</p>' % esc(presentation_objective) if presentation_objective else '',
        titleblock=title_block(tasks, reqs, cover, decisions, working, fields, focused, stamp, method, ui),
        nav=''.join('<a href="#%s">%s</a>' % (anchor, esc(label)) for anchor, label in nav),
        status=status_html, overview=overview_html, graph=graph_html, tasks=tasks_html, architecture=map_html, technical=technical,
        export=export_section(export_ui), footer=footer, print_reports=print_reports, island=island,
        ui_skip=esc(ui['skip']), ui_theme=esc(ui['theme']), ui_nav=esc(ui['nav']), ui_freshness=esc(ui['freshness'].format(built=stamp)))
    try:
        page = fill(template, values)
    except KeyError as missing:
        print('the template names unknown slots: %s' % missing, file=sys.stderr)
        return 2
    # An open file view reloads itself when this revision changes: the page names a sibling stamp script, and
    # the stamp is written after the page so a reader never reloads into a half-written file.
    output = Path(args.output)
    stamp_name = output.stem + '.stamp.js'
    revision = hashlib.sha256(page.encode('utf-8')).hexdigest()[:16]
    meta = '<meta name="tackle-file-revision" content="%s" data-stamp="%s" data-page="%s">' % (
        revision, esc(stamp_name), esc(output.name))
    page = re.sub(r'(?i)(<head\b[^>]*>)', lambda found: found.group(1) + meta, page, count=1)
    stamp = 'window.TacklePlanViewStamp=window.TacklePlanViewStamp||{};window.TacklePlanViewStamp[%s]=%s;\n' % (
        json.dumps(output.name), json.dumps(revision))
    try:
        for target, text in ((output, page + '\n'), (output.with_name(stamp_name), stamp)):
            partial = target.with_name('.' + target.name + '.partial')
            partial.write_text(text, encoding='utf-8')
            os.replace(partial, target)
    except OSError as problem:
        print('cannot write the output: %s' % problem, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
```
