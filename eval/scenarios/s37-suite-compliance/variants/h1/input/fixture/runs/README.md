# Comparison runs — canned-replies test

We're deciding whether to give support agents `canned-replies.md` when they handle a routine ticket, so we ran the same one-line fix to a reply template twice under two conditions:

- `baseline/` — fixed the template without canned-replies.md.
- `treatment/` — fixed the template with canned-replies.md.

Each run folder holds its own copy of the template, a `trace.md` (its actions, in order) and a `writeup.md` (its final write-up). The expected fix is in `ANSWER-KEY.md`.
