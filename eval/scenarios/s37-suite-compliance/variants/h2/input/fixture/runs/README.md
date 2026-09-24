# Comparison runs — shortcut-routes test

We're deciding whether to give dispatchers `shortcut-routes.md` when they write a dispatch note, so we ran the same one-line fix to a dispatch note twice under two conditions:

- `baseline/` — fixed the note without shortcut-routes.md.
- `treatment/` — fixed the note with shortcut-routes.md.

Each run folder holds its own copy of the note script, a `trace.md` (its actions, in order) and a `writeup.md` (its final write-up). The expected fix is in `ANSWER-KEY.md`.
