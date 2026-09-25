GradebookLite tracks student percentages. `report_card(name: str, score: float) -> str` in
`gradebooklite/grades.py` already prints one student's rounded percentage and letter grade, as a
single line like `"Alice: 92% (grade A)"`.

Teachers also want a whole-class view. Add `class_report(scores: dict[str, float]) -> str` to
`gradebooklite/grades.py`: it takes a mapping of student name to raw percentage (0-100), and returns
one `report_card`-formatted line per student, joined by newlines, ordered from the highest percentage
to the lowest, with any students who show the same percentage ordered alphabetically by name.
