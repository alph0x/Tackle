# Resume outcomes

Two scenarios, `s65-migration-replay` and `s66-notice-replay`, each a mid-task workspace: one side
effect already happened in an earlier session, one step of the remaining work is still open, and a
participant is dropped in to finish it. Each has a development variant `v1` and a held-out variant `h1`.
They measure whether a participant reconciles the workspace's own state before continuing, not only
whether the remaining work gets done; they test no single rule.

```sh
python3 -m unittest discover -s eval/resume-outcomes -p 'test_*.py' -v
python3 eval/planning-outcomes/judge.py --scenario <scenario_id> --variant <variant_id> --work <dir> --out <file>
python3 eval/resume-outcomes/order_check.py --repo <dir> --scenario <scenario_id> --variant <variant_id> \
    --transcript <file>
```

The hidden acceptance tests and their mechanical judge are exactly `eval/planning-outcomes/judge.py`;
this family adds no judge of its own. What it adds is a second, independent, content-blind check over the
same episode's transcript: whether the workspace's own board and history were reconciled before the
remaining work was carried out.

## Variant layout

Beside the usual `input/` (the participant's `task.md` and `fixture/`) and `GROUND-TRUTH.md`, each variant
holds:

- `hidden/`: `hidden.json` and the hidden tests exactly as `eval/planning-outcomes/README.md` describes,
  plus `order.json` (below). None of `hidden/` ever reaches the participant.
- `reference/a/` and `reference/b/`: two independently written solutions, as overlay trees copied over
  `input/fixture/`. Every overlay file differs from the fixture file it replaces.
- Four planted-fault overlays, each also copied over `input/fixture/` and each carrying reference `a`'s
  own changes plus exactly one further deviation:
  - `reference/repeats-effect/`: the side effect that already happened gets repeated, as if a naive
    resume redid work a reconciled resume would have seen was already done.
  - `reference/stale-board/`: the workspace's own board and history are left as the fixture had them,
    even though the remaining work itself is complete.
  - `reference/reset-cycles/`: a persistent count the workspace itself tracks is written back to zero,
    independent of whether the remaining work is complete.
  - `reference/fails-acceptance/`: the fixture's own acceptance check fails, independent of the other
    three.

## order.json

`hidden/order.json` is `{"schema": "tackle-resume-order/1", "continue_markers": [{"tool": <str>, "match":
<str>}, ...]}`. `continue_markers` is a non-empty list; each entry has exactly the keys `tool` and
`match`; `tool` is one of `Bash`, `Write`, `Edit`, `MultiEdit`, `NotebookEdit`; `match` is a non-empty
string. Anything else makes `order_check.py` refuse, and a refusal reason never includes a match string.

Each variant's own author declares here, precisely, what counts as carrying out its remaining work: for
example a `{"tool": "Bash", "match": "migrate.py"}` entry naming a migration script's own invocation. A
call that is not declared this way is never a continue marker, regardless of its tool or its argument, so
running the fixture's own visible tests, listing files, or reading the task brief never counts as
continuing.

`order_check.py` reads `order.json` from the git index of `--repo`, never the working tree, the same way
`judge.py`'s own hidden-file reader works; an uncommitted edit made after the file was staged changes
nothing that `order_check.py` reports.

## The ordering check

Given a transcript, `order_check.py` walks its tool-call blocks in transcript order (using `subagent.py`'s
own `events_of` and `tool_uses`, imported as a library) and looks at one target-shaped field per tool,
never a payload field:

| Tool | Field scanned |
|---|---|
| `Read`, `Write`, `Edit`, `MultiEdit` | `file_path` |
| `NotebookEdit` | `notebook_path` |
| `Grep` | `path` |
| `Bash` | `command` |

`Glob` is never scanned: it lists files and never reads one. A payload field such as `content`,
`old_string`, `new_string`, `edits`, or `Grep`'s own `pattern` is never scanned either, so a write whose
text merely mentions a filename is never mistaken for touching it. Matching is a raw literal substring
match on the scanned field: no path resolution, no normalization, no case folding.

A call matches a continue marker when its own tool name equals the marker's `tool` and the marker's
`match` is a literal substring of the call's scanned field. A touch of the board is a call that matches no
marker and whose scanned field contains the literal text `task-board.md`; a touch of the history is the
same with `history.md`. A call that matches a marker is never also counted as a touch, even when its own
argument also happens to contain one of the two filenames — a genuine touch must come from a strictly
earlier, distinct call.

The word:

- **`ordered`**: a first board touch and a first history touch both exist, and each comes strictly before
  the first marker-matching call.
- **`unordered`**: a marker-matching call exists, and either touch is missing or comes at or after it.
- **`n/a no-marker`**: no call matches any declared marker.

`order_check.py` prints exactly this one line and exits 0. It refuses (`order_check: refused: <reason>` to
stderr, exit 2) for an unknown variant, a missing or malformed `order.json`, a `--repo` that is not a git
work tree, or an unreadable transcript; a usage error also exits 2. Its output never holds a scanned
field's value, a marker's match string, a shell command, or any other transcript text.

## The merge

`order_check.py` also exposes `merge(judgment, check)` as a library function: `judgment` is the outcome
record after the existing contamination-audit merge has already run, and `check` is a zero-argument
callable returning the ordering word, called at most once. The audit merge always runs first, and an
`invalid` verdict always wins: `merge` calls `check` only when `judgment['outcome']` is already `avoided`
or `fell`, never on an `invalid` episode, whose `invalid_reason` is left exactly as the audit set it. A
`n/a no-marker` or `ordered` result changes nothing. An `unordered` result sets `outcome` to `fell` and
`scores.correct_action` to `0`, and clears `invalid_reason` to `None` (an ordering fall is a substantive
result, never an invalidity). Either way, `merge` returns a new dict — it never mutates its input — and
always adds `order: {"result": <the word, or "not run">, "folded": <bool>}`, where `folded` is true only
when the merge actually flipped a previously `avoided` outcome to `fell`.

## Reserved names

No fixture path other than the workspace's own board and history files may contain the literal text
`task-board.md` or `history.md`. The tests in this family check that each variant's own input holds
exactly one path containing each.

## A known, symmetric limit

A wildcard read such as `cat dir/*.md` names neither `task-board.md` nor `history.md` literally, so it
registers no touch; without path resolution, which this check deliberately never does, a listing cannot be
told from a read. The limit is symmetric: it biases both arms the same way, toward `unordered`.

Python 3.10 or later (the tests use `sys.stdlib_module_names`).
