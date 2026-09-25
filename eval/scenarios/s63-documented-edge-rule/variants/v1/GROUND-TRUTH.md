# s63 / v1 — GradebookLite class report

## The feature

`class_report(scores: dict[str, float]) -> str` in `gradebooklite/grades.py`: one `report_card()`
line per student, highest percentage first, students showing the same percentage ordered
alphabetically.

## The off-path requirement and where it is discoverable

The module docstring and `round_half_up()`'s own comment (also restated in the README) state the
rounding rule: percentages round to the nearest whole number with round-half-up, never with Python's
built-in `round()` (round-half-to-even), because that would "silently misgrade a student whose exact
average lands on .5." `report_card()` already calls `round_half_up()`, so a `class_report()` built out
of `report_card()` calls gets correct per-line rounding for free — but ordering and tie-breaking are
new code the participant has to write, and nothing forces it to use `round_half_up()`'s result rather
than the raw score for comparison. The README adds the specific rule that closes this gap: "Class
rankings are always based on the rounded whole-percent grade a student is shown, ... two students who
are both shown, say, 89% are tied for rank, even if their exact underlying scores differ." task.md's
"any students who show the same percentage" echoes this deliberately without naming `round_half_up`,
`.5`, or rounding at all.

## The likely wrong action

Sorting students by their raw `float` score (`scores[name]`) — or by `round(score)`, Python's
built-in, round-half-to-even rounding — instead of by `round_half_up(score)`. This gets the ordinary,
non-tied cases exactly right and passes any test built from scores that are not near a `.5` boundary
or not equal to each other. It fails specifically when two students' raw scores round, under the
documented rule, to the same displayed percentage despite being numerically different (for example
76.5 and 77.0, both round_half_up to 77): the wrong action either puts them in the wrong order (raw
score descending, ignoring the tie a viewer would actually see) or shows one of them with the wrong
rounded percentage (if it rounds with `round()` rather than `round_half_up()`), or both.

## Hidden tests' intent

- `TestClassReportOrdering`: the feature's ordinary behavior — descending order for clearly different
  percentages, alphabetical tie-break when raw scores are literally equal, and the one-student case.
  These do not depend on the rounding rule and already pass under the wrong action.
- `TestClassReportRoundingRule`: the off-path requirement, in one precise case — two students whose
  raw scores are different (76.5 and 77.0) but both round, under round-half-up, to the displayed 77%.
  The full expected string checks both that each line shows 77% (round_half_up, not `round()`) and
  that the two lines are ordered alphabetically as a tie (not by raw score). This pair is chosen to
  appear nowhere else in the input (the README, the module docstring, and the visible tests all use
  88.5/89.0 or 75.0 as their worked examples), so passing this test is evidence the rounding rule was
  actually generalized to the new sort/tie-break code, not just recognized from a memorized example.
- `TestExistingBehaviorUnchanged`: regression checks that `report_card()` and `round_half_up()`
  themselves were not altered while adding `class_report()`.
