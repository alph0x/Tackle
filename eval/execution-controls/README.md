# Full execution-control regressions

Run `python3 -m unittest discover -s eval/execution-controls -v` from the repository root.
The suite executes the Python blocks extracted from `references/guides/full-checks.md`.
It checks real child failures, binary streams, timeouts/signals, input/script snapshots,
missing and additive tests, immutable observations, literal canonical command extraction,
source/slug rejection and row-specific stdout/exit interpretation.

These deterministic checks do not prove an agent adopts the recipe, select all semantic inputs,
or establish native filesystem confinement. Those require separately registered behavioral and
capability observations. No executable is added to the Markdown-only install artifact.
