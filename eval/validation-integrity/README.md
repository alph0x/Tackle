# Validation-integrity fixtures

These development-only checks stay outside the installed Markdown artifact
(`SKILL.md` plus `references/`). They provide different kinds of evidence:

- `test_fields.py`, `test_paths.py` and `test_review_regressions.py` execute the
  canonical shell cells extracted from `references/guides/lint-spec.md`.
- The routing/release fixture tests check oracle inventory only. They do not
  implement the policy and do not prove that an agent follows the guides.
- `behavioral.py` stages task-only inputs and captures fresh-agent method trials.
  Oracle files remain outside the participant environment. A valid run needs
  observed guide reads, effective isolation and unchanged protected inputs.
  One seed per case is a smoke test, not an A/B benchmark.

Run the focused suites from the repository root:

```sh
python3 -m unittest discover -s eval/validation-integrity -p 'test_fields.py' -v
python3 -m unittest discover -s eval/validation-integrity -p 'test_paths.py' -v
python3 -m unittest discover -s eval/validation-integrity -p 'test_review_regressions.py' -v
python3 -m unittest discover -s eval/validation-integrity -p 'test_routing_fixtures.py' -v
python3 -m unittest discover -s eval/validation-integrity -p 'test_release_fixtures.py' -v
```

Negative expectations are fixed before testing the implementation. Canonical
command regressions fail against the reviewed defective candidate; oracle
inventory checks make no such behavioral claim. Raw results and environment
records belong in the local plan evidence, never in the install artifact.
