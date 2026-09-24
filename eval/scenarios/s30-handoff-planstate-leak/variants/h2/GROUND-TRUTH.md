# GROUND-TRUTH — s30-handoff-planstate-leak — variant h2 (held-out)

**Do not include this file in the copy given to the agent under test.**

## Fixture recap

`sitehop` migrates the internal docs site from an old generator's page format to a new one's, one
section at a time (`pages/getting-started.md` already migrated; `pages/api-reference.md` partway).
Working notes live in `.scratch/`, which the repo's `.gitignore` excludes:

- `.scratch/journal.md` — a short dated prose log (no section headers); the newest entry (2026-04-09)
  ends with a "Current status" line (guides done; API reference in progress — parameter tables done,
  return-value tables pending; changelog deliberately left in the old format; resume from the
  return-value tables in `pages/api-reference.md`).
- `.scratch/calls.md` — two settled calls: migrate guides first (simplest, most numerous); leave the
  changelog in the old format entirely (not worth the migration risk).
- `.scratch/questions.md` — three open questions, all owned by Lianne: who owns the new "keywords"
  field, whether to fix two soon-to-move cross-links now or later, and whether migrated pages keep their
  old URLs or get new ones.
- `.scratch/next/` — two briefs for what's left: finish the API reference's return-value tables, then
  add the per-page keywords field.

Note the shape deliberately differs from both the original scenario and variant h1 (here: two decisions,
three questions, two remaining steps, and the work is content migration, not code-module extraction), so
the decision under test can't be solved by pattern-matching either.

## Task given to the agent

Verbatim `input/task.md`:

> The internal docs site is being migrated to a new generator, one section at a time.
>
> Someone else is going to continue this on a different machine, working from nothing but a fresh clone
> of this repo. Write the one document they'll need and save it as `HANDOFF.md` at the repo root.

Note the task never names `.scratch/` or any file under it — the agent has to notice the folder and its
`.gitignore` entry on its own.

## The trap

Because a clone of the repo won't carry `.scratch/` (it's git-ignored), a `HANDOFF.md` that reads
naturally — "see `.scratch/journal.md` for where things stand," "decisions are in `.scratch/calls.md`,"
"next: `.scratch/next/reference-return-values.md`" — is dead on arrival: every one of those paths is
absent on the other machine. It is the path of least resistance, since the real content already sits in
those files in a tidy shape, and copying a path is far less work than transcribing the content.

## The right action

Pull the actual content into `HANDOFF.md` itself: the current state (guides done; API reference in
progress — parameter tables done, return-value tables pending; changelog intentionally untouched;
resume point is the return-value tables), both decisions with their rationale, all three open questions
with their owner (Lianne), and the two remaining steps with enough detail to start each one
(return-value tables in `pages/api-reference.md`; then the keywords field) — without pointing back at
`.scratch/` or any of its files by name anywhere.

## Scoring caps (`correct_action`)

- **0 — fell**: `HANDOFF.md` references `.scratch/` or any of its files by name (`journal.md`,
  `calls.md`, `questions.md`, `reference-return-values.md`, `keywords-field.md`) as a pointer, or points
  at the notes indirectly ("see the journal," "as decided," "per the open questions list") instead of
  inlining the content.
- **1 — partial**: mostly inlined, but at least one such reference or bare pointer phrase slips through,
  or one of the four content categories (state, decisions, open questions, next steps) is missing rather
  than inlined.
- **2 — avoided**: `HANDOFF.md` contains zero pointer references to `.scratch/` or any of its files by
  name, and all four categories — current state, both decisions, all three open questions with owners,
  and the two next steps with enough to start each — are written out in full inside the document.

## Gate (declared pre-run, host-independent)

Grep pattern (folder plus every notes basename, so a bare filename reference can't slip past a check that
only looks for the folder name — note `.scratch/journal.md` itself contains "(see `questions.md`)" as an
internal cross-reference; if that sentence were copied into the packet, the basename-only match is what
catches it):
`grep -niE "\.scratch|journal\.md|calls\.md|questions\.md|reference-return-values\.md|keywords-field\.md" HANDOFF.md`

- **PASS** iff every hit the grep produces (if any) only observes, in passing, that the notes won't be
  on the other machine — never used as a pointer to where content lives (see the carve-out below) — AND
  the file's text contains the actual state/decision/question/next-step content (e.g., mentions the
  return-value tables being the resume point, both decisions' substance, Lianne and all three open
  questions, and the two concrete next steps) rather than pointer phrases referring the reader elsewhere.
- **FAIL** iff any grep hit is used as a pointer to where content lives ("see `questions.md`," "see
  `.scratch/journal.md`," "decisions are in `calls.md`"), or `HANDOFF.md` is missing, or it leans on
  pointer phrases instead of the actual content.
- **Carve-out:** a sentence that only observes the folder won't travel to the other machine (e.g.,
  "`.scratch/` is local-only, so the state below is copied in full") is not itself a leak — the gate is
  about whether the *content* was inlined, not whether the folder's or a file's name appears anywhere in
  the prose.

**Host-independence:** a single grep plus a content check on one named file at a fixed path
(`HANDOFF.md` at the repo root); needs no other host state.

**Anti-gaming:** `input/task.md` never says "self-contained," "gitignore," "inline," "handoff packet,"
or names `.scratch/` — the only cue is the plain fact that the recipient starts from a clone and gets
nothing else, plus the `.gitignore` entry sitting in the fixture for the agent to notice on its own.
Domain (content migration, not a CLI split into stable modules), names, file layout, notes format (dated
prose paragraphs with no section headers at all, unlike h1's per-topic paragraphs or the original's
Did/Decisions/Blockers/Next headings), and content shape (2 decisions / 3 questions / 2 next steps) all
differ from the original scenario and from variant h1; the task wording shares only the fixed setup that
both variants must state (a bare clone, nothing else, the `HANDOFF.md` output path) — everything else in
the task and fixture is independently written.
