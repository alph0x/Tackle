# Project validator

The example validator in `extras/validator-example.md` runs through the invocation the verify guide defines (`<command> <workspace>` from the repository root) over workspaces the test builds in a temporary directory: a clean brief, a missing target, a target added by a write scope, a closed brief and an empty existing file, plus the usage error. The guide section is checked for the declaration rule, the output line and the exit contract.
