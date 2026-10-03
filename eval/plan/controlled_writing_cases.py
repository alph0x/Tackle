"""Fixture texts for the controlled-writing recipe.

Compliant sentences hold at most twelve words and long ones forty-five or more, so any limit the guide
sets between 20 and 35 words judges them the same way. Each case is (name, text, language, expected),
where expected is empty (no finding) or a list of (kind, line) pairs that must each be reported.
"""

LONG_EN = ('The executor reads the brief and the named inputs and then it runs the selected checks over the '
           'complete case matrix and it records every result together with the command and the working directory '
           'and the exit code before it reports back to the coordinator about the outcome.')
LONG_ES = ('El ejecutor lee la tarea y las entradas nombradas y después ejecuta las comprobaciones elegidas sobre '
           'toda la matriz de casos y registra cada resultado junto con la orden y el directorio de trabajo y el '
           'código de salida antes de informar al coordinador sobre el resultado final.')
LONG_DE = ('Der Ausführende liest die Aufgabe und die genannten Eingaben und führt danach die ausgewählten Prüfungen '
           'über die gesamte Fallmatrix aus und er speichert jedes Ergebnis zusammen mit dem Befehl und dem '
           'Arbeitsverzeichnis und dem Rückgabewert bevor er dem Koordinator über das Ergebnis berichtet.')
SHORT_EN = 'The check reads the board.\nIt reports each failure once.\n'
SHORT_ES = 'La comprobación lee el tablero.\nInforma cada fallo una vez.\n'


def cases():
    """Return the fixture cases; identifiers are built at run time, never stored."""
    task_id = '-'.join(['T', '15'])
    decision_id = '-'.join(['D', '42'])
    digest = 'ab12' * 16
    id_heavy = ('The brief for %s cites %s and %s and %s and %s and %s and %s and %s and %s and %s '
                'and %s and %s and %s and %s and %s ends here today.'
                % ((task_id, decision_id, digest) + (decision_id,) * 12))
    return [
        ('short-english', SHORT_EN, 'en', []),
        ('fenced-code', 'Run this:\n\n```sh\n# %s\n```\n' % LONG_EN, 'en', []),
        ('inline-code', 'The tool printed `%s` and stopped.\n' % LONG_EN, 'en', []),
        ('straight-quotes', 'The owner wrote "%s" in the request.\n' % LONG_EN, 'en', []),
        ('curly-quotes', 'The error read “%s” at start.\n' % LONG_EN, 'en', []),
        ('blockquote', '- **Clause**:\n\n  > %s We leverage various tools, etc.\n' % LONG_EN, 'en', []),
        ('table-row-length', '| Case | Text |\n|---|---|\n| one | %s |\n' % LONG_EN, 'en', []),
        ('anchor-and-comment', '<a id="x"></a>\n<!-- %s -->\nThe board is current.\n' % LONG_EN, 'en', []),
        ('multi-line-comment', '<!--\n%s\n-->\nThe board is current.\n' % LONG_EN, 'en', []),
        ('ids-skip-the-count', id_heavy + '\n', 'en', []),
        ('short-spanish', SHORT_ES, 'es', []),
        ('list-items-without-periods',
         ''.join('- item %d names one short concrete step\n' % i for i in range(8)), 'en', []),
        ('semicolon-clauses',
         'Forbidden: ' + '; '.join('clause %d stays short' % i for i in range(12)) + '.\n', 'en', []),
        ('bold-labels', ''.join('**Label %d.** This sentence stays short. ' % i for i in range(5)) + '\n', 'en', []),
        ('heading-boundaries',
         ' '.join(['word'] * 12) + '\n# ' + ' '.join(['heading'] * 12) + '\n' + ' '.join(['tail'] * 11) + ' end.\n',
         'en', []),
        ('capitalised-vague', 'Various checks run here.\n', 'en', [('vague', 1)]),
        ('lone-quote-then-long', 'The limit is 27" in the old notes. ' + LONG_EN + '\n', 'en', [('long-sentence', 1)]),
        ('long-english', 'Intro line.\n\n%s\n' % LONG_EN, 'en', [('long-sentence', 3)]),
        ('vague-english', 'We leverage various robust synergies, etc.\n', 'en', [('vague', 1)]),
        ('long-after-short-on-one-line', 'It is short. %s\n' % LONG_EN, 'en', [('long-sentence', 1)]),
        ('long-wrapped-over-lines', 'First line.\n%s\n' % LONG_EN.replace(' and then ', '\nand then '), 'en',
         [('long-sentence', 2)]),
        ('vague-in-table', '| Case | Text |\n|---|---|\n| one | We leverage various synergies, etc. |\n', 'en',
         [('vague', 3)]),
        ('long-spanish', 'Inicio.\n\n%s\n' % LONG_ES, 'es', [('long-sentence', 3)]),
        ('vague-spanish', 'Aprovechamos varias sinergias robustas, etcétera.\n', 'es', [('vague', 1)]),
        ('long-other-language', '%s\n' % LONG_DE, 'de', [('long-sentence', 1)]),
        ('long-list-item', '- first item\n- %s\n' % LONG_EN, 'en', [('long-sentence', 2)]),
        ('vague-multiword-phrase', 'We act in order to\nreduce risk.\n', 'en', [('vague', 1)]),
        ('vague-skipped-in-other-language', 'We leverage various robust synergies, etc.\n', 'de', []),
    ]
