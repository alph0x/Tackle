# shelfmark

Circulation tooling for the Harrow Lane Community Library.

- `python3 -m notices render <loans.json> <YYYY-MM-DD> <outdir>` writes one overdue notice per patron
  (`<card_no>.txt`) from the circulation desk's loans export.
- Wording: `docs/notice-wording.md`. Tests: `python3 -m unittest discover -s tests -q`.
- Acceptance of the notices work: `sh checks/accept.sh`.

Planning: `docs/plans/overdue-notices/`.
