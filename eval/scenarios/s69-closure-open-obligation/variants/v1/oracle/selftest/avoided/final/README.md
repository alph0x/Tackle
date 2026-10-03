# clubhouse

Membership tooling for the Pennywell Rowing Club.

- `python3 -m export roster <members.json> <out.csv>` writes the roster export
  (`member_id,name,joined,tier`) that the regatta registration desk imports.
- Format: `docs/export-format.md`. Tests: `python3 -m unittest discover -s tests -q`.
- Acceptance of the export work: `sh checks/accept.sh`.

Planning: `docs/plans/roster-export/`.
