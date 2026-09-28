# Validation-integrity fixtures

These development-only checks stay outside the installed Markdown artifact
(`SKILL.md` plus `references/`). They provide different kinds of evidence:

- `test_fields.py`, `test_paths.py` and `test_dependency_and_scope_parsing.py` execute the
  canonical shell cells extracted from `references/guides/lint-spec.md` (lint rows) and
  `MAINTAINING.md` (release gates).

Run the focused suites from the repository root:

```sh
python3 -m unittest discover -s eval/validation-integrity -p 'test_fields.py' -v
python3 -m unittest discover -s eval/validation-integrity -p 'test_paths.py' -v
python3 -m unittest discover -s eval/validation-integrity -p 'test_dependency_and_scope_parsing.py' -v
```

Negative expectations are fixed before testing the implementation. Canonical
command regressions fail against the reviewed defective candidate. Raw results and environment
records stay local and never enter the install artifact; tracked run records,
their hashes and the claim map live in [`eval/records/`](../records/README.md).
