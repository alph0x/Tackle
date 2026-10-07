# plotbook

Small tools for the Larkfield Allotment Society's treasurer.

- `python3 -m statements render <plots.csv> <season> <out.txt>` writes one fee statement per plot, ready to
  print and post before the season's fees fall due.
- Statement layout: `docs/statement-format.md`. Tests: `python3 -m unittest discover -s tests -q`.
- Acceptance of the statements work: `sh checks/accept.sh`.

Planning: `docs/plans/fee-statements/`.
