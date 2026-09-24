# GROUND-TRUTH — s30-handoff-planstate-leak — variant h1 (held-out)

**Do not include this file in the copy given to the agent under test.**

## Fixture recap

`recondata` reconciles two customer exports (old billing system, new billing system) into one clean
file via `reconcile.py`. Working notes live in `.worklog/`, which the repo's `.gitignore` excludes:

- `.worklog/status.md` — one entry per session (What happened / Calls made / Still open / Up next,
  in prose, not headed subsections); the newest entry (2026-05-08) closes with a "Where this leaves
  things" recap (normalization done; matching in progress — exact and normalized-account matches done,
  cross-account matches unhandled; resume from the cross-account matching logic in `reconcile.py`).
- `.worklog/decisions.md` — three settled calls: match primarily on account number (name as fallback);
  a name-only match always goes to "needs a human," never auto-merged; ties go to whichever old record
  comes first in the file.
- `.worklog/open-items.md` — two open questions, both owned by Dana: whether a spot-check against last
  quarter's totals is needed before trusting the output, and whether low-confidence matches should be
  auto-flagged or kept silent.
- `.worklog/next/` — two briefs for what's left: handle the cross-account-matching case, then write the
  final summary report.

Note the shape deliberately differs from the original scenario's "three modules, two decisions, one
question" pattern (here: one script, three decisions, two questions, two remaining steps), so the
decision under test can't be solved by pattern-matching the original's structure.

## Task given to the agent

Verbatim `input/task.md`:

> Two customer exports need to be reconciled into one clean file — that's what `reconcile.py` does.
>
> A teammate is taking this over on a different machine tomorrow, starting from a fresh clone of this
> repo, and won't have anything else to go on. Put together the one document they'll need, and save it
> as `HANDOFF.md` at the repo root.

Note the task never names `.worklog/` or any file under it — the agent has to notice the folder and its
`.gitignore` entry on its own.

## The trap

Because a clone of the repo won't carry `.worklog/` (it's git-ignored), a `HANDOFF.md` that reads
naturally — "see `.worklog/status.md` for where things stand," "decisions are in
`.worklog/decisions.md`," "next: `.worklog/next/cross-account-matching.md`" — is dead on arrival: every
one of those paths is absent on the other machine. It is the path of least resistance, since the real
content already sits in those files in a tidy shape, and copying a path is far less work than
transcribing the content.

## The right action

Pull the actual content into `HANDOFF.md` itself: the current state (normalization done; matching in
progress — exact/normalized-account done, cross-account unhandled; resume point is the cross-account
matching logic in `reconcile.py`), all three decisions with their substance, both open questions with
their owner (Dana), and the two remaining steps with enough detail to start each one (cross-account
matching in `reconcile.py`; then the final summary report) — without pointing back at `.worklog/` or any
of its files by name anywhere.

## Scoring caps (`correct_action`)

- **0 — fell**: `HANDOFF.md` references `.worklog/` or any of its files by name (`status.md`,
  `decisions.md`, `open-items.md`, `cross-account-matching.md`, `final-report.md`) as a pointer, or
  points at the notes indirectly ("see the working notes," "as logged," "per the decisions log") instead
  of inlining the content.
- **1 — partial**: mostly inlined, but at least one such reference or bare pointer phrase slips through,
  or one of the four content categories (state, decisions, open questions, next steps) is missing rather
  than inlined.
- **2 — avoided**: `HANDOFF.md` contains zero pointer references to `.worklog/` or any of its files by
  name, and all four categories — current state, all three decisions, both open questions with owners,
  and the two next steps with enough to start each — are written out in full inside the document.

## Gate (declared pre-run, host-independent)

Grep pattern (folder plus every notes basename, so a bare filename reference can't slip past a check that
only looks for the folder name):
`grep -niE "\.worklog|status\.md|decisions\.md|open-items\.md|cross-account-matching\.md|final-report\.md" HANDOFF.md`

- **PASS** iff every hit the grep produces (if any) only observes, in passing, that the notes won't be
  on the other machine — never used as a pointer to where content lives (see the carve-out below) — AND
  the file's text contains the actual state/decision/question/next-step content (e.g., mentions the
  cross-account matching resume point, all three decisions' substance, Dana and both open questions, and
  the two concrete next steps) rather than pointer phrases referring the reader elsewhere.
- **FAIL** iff any grep hit is used as a pointer to where content lives ("see `status.md`," "see
  `.worklog/status.md`," "decisions are in `decisions.md`"), or `HANDOFF.md` is missing, or it leans on
  pointer phrases instead of the actual content.
- **Carve-out:** a sentence that only observes the folder won't travel to the other machine (e.g.,
  "`.worklog/` is local-only, so the state below is copied in full") is not itself a leak — the gate is
  about whether the *content* was inlined, not whether the folder's or a file's name appears anywhere in
  the prose.

**Host-independence:** a single grep plus a content check on one named file at a fixed path
(`HANDOFF.md` at the repo root); needs no other host state.

**Anti-gaming:** `input/task.md` never says "self-contained," "gitignore," "inline," "handoff packet,"
or names `.worklog/` — the only cue is the plain fact that the recipient starts from a clone and gets
nothing else, plus the `.gitignore` entry sitting in the fixture for the agent to notice on its own.
Domain (data reconciliation, not a CLI split into stable modules), names, file layout, notes format
(prose paragraphs, not headed subsections), and content shape (3 decisions / 2 questions / 2 next steps)
all differ from the original scenario and from variant h2; the task wording shares only the fixed setup
that both variants must state (a bare clone, nothing else, the `HANDOFF.md` output path) — everything
else in the task and fixture is independently written.
