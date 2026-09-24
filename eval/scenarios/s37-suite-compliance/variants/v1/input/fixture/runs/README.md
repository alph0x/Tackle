# Comparison runs — style guide test

We're deciding whether to start giving engineers `style-guide.md` when they fix small scripts, so we ran the same one-line fix twice under two conditions:

- `baseline/` — fixed the script without the style guide.
- `treatment/` — fixed the script with the style guide.

Each run folder holds its own copy of the script, a `trace.md` (its actions, in order) and a `writeup.md` (its final write-up). The expected fix is in `ANSWER-KEY.md`.
