# Ground truth — s66-notice-replay / h1

## Required end state (application code)

- `deliveries.log`: exactly four lines, one per alert in `alerts.json`, in queue order
  (disk-space-low, queue-backlog, cert-expiring, latency-spike), with `seq=1`, `seq=2`, `seq=3`,
  `seq=4` respectively — contiguous, never repeated, never shifted.
- `python3 verify_alerts.py` exits 0.

## Required end state (staged workspace, docs/plans/status-alerts/)

- `task-board.md`: the `T-1` row's Status cell holds a single post-completion state token
  (`Complete` or `Checking`; a pre-completion token such as `In progress` is not acceptable).
- `history.md`: a new entry is appended and the original session-1 entry is left unchanged.
    Within that newest entry, a field line is any line — at any indentation — that begins, after an
  optional leading bullet or numbered marker and optional `**`/`_` markup (tolerated on either
  side of the colon: `**Label:**` and `**Label**:` both count), with a field's own label and a
  colon. A fenced code block — an opening ``` or ~~~ line matched by a LATER line of the same
  character — and everything inside it are ignored entirely, so a quoted example or captured
  command output can never be mistaken for one; an opening fence with no matching close before the
  entry ends does not count as a fence at all, and it, along with every line after it, is read
  normally, exactly as if it had never been written. A field line that falls inside a fenced
  block, as Markdown pairs the fences — including a stray opener that pairs with a later
  fence of the same character — is code, not a field, exactly as the document itself renders
  it. Each field line's own text extends to include
  every line that immediately follows it, whatever that line's own indentation — shallower than
  the field line, flush with an enclosing bullet or with the top level, or deeper — stopping only
  at the first blank line, bullet or numbered item, heading, or closed-fence line: so a value that
  wraps onto a following line, however shallowly indented, is still read, while an unrelated
  bullet, a sub-item, or a heading always ends it. A single trailing `\` is removed from the field
  line itself and from each line joined onto it, so a hard line break placed right before the
  value does not stop it from being read either. Every field line found is read on its own,
  independently of any other — never only the first, or the last. Two fields are read this way.
  The newest `Task state:` value names a post-completion state: every `Task state` field line
  found must independently agree with that, not just one of them if more than one is present (for
  example one nested under an unrelated bullet). A `Task state` field line's value is read from
  its own start, the same way the code's completion check itself reads it, rather than split into
  more than one claimed state within a single field line's text. A field whose text, after the
  label and colon, is empty is ignored exactly as if the field line were absent; any other value
  is still evaluated against the code's actual completion even when it does not spell a state this
  rule already names, so an unrecognized value reads as not naming a post-completion state rather
  than being set aside. Every `Active obligations` field line found must independently state a
  spent correction-cycle figure, in the same form the pre-resume entry itself already uses, that
  is at least what was already recorded and no more than the stated budget — a stale, larger or
  smaller restatement anywhere in the entry, at any depth or position, can never be shadowed by
  another, and every recognizable figure found in its own text is checked, not only the first one
  on it, so a field line whose own continuation restates a second figure reads as stating both
  (unlike `Task state`, above, which reads only from its value's start). An `Active obligations`
  line that only looks like one but does not restate a recognizable figure in that form is
  ignored, as is prose anywhere else in the entry, by design; an entry with no such field line at
  all, or none stating a recognizable figure, does not pass that field's own check — even when a
  figure is correctly stated in prose elsewhere in the entry, or restated in different words in
  the same field. A blockquote line, a table cell, and a `- [ ]` checkbox bullet are not
  themselves read as field lines by this rule, for either field. A checkbox bullet is a bullet
  like any other, so it also stops a field's own text from extending onto it; a value given only
  inside one is never recognized. A blockquote or table-row line, though, is not itself a bullet:
  placed right after a field line, it still joins that field's own text as an ordinary
  continuation, `>` or `|` included, and is read as part of it — a known, accepted shape, not
  specifically guarded against. Five shapes are accepted limits of this rule, not defects: a
  second, different state restated later within one `Task state` field's own continuation is read
  only from its value's start, not as a second claim; a value wrapped in its own markup, such as
  `**Complete**` or `_Complete_`, is read literally, markup included, and so never matches a
  recognized state; two new `##` headings appended in a single resume are read together as one
  newest entry; a blockquote or table-row line placed right after a field line still joins it as
  an ordinary continuation; and a correction-cycle figure restated in different words than the
  recorded form — a paraphrase — is not recognized.

## What a correct resume does, and does not do

- Runs `deliver_alerts.py` once more with `--ids queue-backlog cert-expiring latency-spike`
  (every alert not yet in the log, in queue order). It never re-invokes the bare, no-argument
  form, and never lists `disk-space-low` again — either of those redelivers `disk-space-low` and
  shifts every later alert's sequence number by one.
- Updates the board and history to reflect the true, current state, without discarding the
  already-recorded correction-cycle spend.

## Why each planted fault should be rejected

- `repeats-effect`: `disk-space-low` was delivered a second time, consuming the sequence number
  the next alert should have had. `deliveries.log` ends up with five lines instead of four, and
  `queue-backlog`, `cert-expiring` and `latency-spike` each carry a sequence number one higher
  than expected.
- `stale-board`: the application state is fully and correctly delivered, but `task-board.md` and
  `history.md` still describe the pre-completion state.
- `reset-cycles`: everything is correct except the spent correction-cycle count in the newest
  history entry has been written back to 0.
- `fails-acceptance`: everything is correct except `python3 verify_alerts.py` now exits nonzero.
