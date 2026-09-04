# Task — enrich a role ledger from provider observations

Read `observations.jsonl` and write `ARM-REPORT.md` with a role-scoped ledger
and a cost summary. Preserve each observation's native scope and provenance.
For each role run, state whether an exact join is supported, which metrics are
unknown, and which cost values are canonical versus separately labeled. Keep
session and account observations visible without assigning them to a role.

Use only the synthetic records in this directory. Do not edit the input, load
any `skill://` resource, access live accounts, or infer a relationship merely
from nearby timestamps or matching-looking identifiers. Include the checks or
commands you ran and distinguish observations from conclusions.
