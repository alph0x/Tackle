# GradebookLite

A tiny grading tool.

## Layout

- `gradebooklite/grades.py` — percentages, rounding, letter grades, and per-student report lines.
- `gradebooklite/roster.py` — loads a roster of raw scores from a simple text file.

## Running the tests

```sh
python3 -m unittest discover -s tests -v
```

## Rounding

Percentages are always rounded to the nearest whole number with round-half-up (a tie rounds away from
zero: 88.5 becomes 89), matching the registrar's grading policy — never Python's built-in `round()`,
which rounds half to even and would silently misgrade a student whose exact average lands on `.5`. See
`round_half_up()` in `gradebooklite/grades.py`, which every report in this module is built from.

Class rankings are always based on the rounded whole-percent grade a student is shown, never on
fractional points a student never sees: two students who are both shown, say, 89% are tied for rank,
even if their exact underlying scores differ.
