# Deterministic tests

Tests live under `eval/tests/`, grouped by the guarantee they protect. Test tools,
synthetic fixtures and frozen cohort implementations retain their original paths.
`suite-manifest.json` is the complete discovery registry: its `path` locates tests,
`source` locates their tools/fixtures, and `category` explains their purpose.
Every family also declares its functional `purpose`; [the suite index](tests/README.md)
lists those guarantees. Name suites for behavior, such as `verdicts/no-regression`
or `verdicts/resume-comparison`, without dates, session labels or candidate ordinals.
Sealed evidence keeps its archival identifiers in source metadata.

| Directory | Purpose | Run when |
|---|---|---|
| `tests/product/` | Shipped instructions, templates, lint contracts, installation and migration | Their artifact or consumer changes; final integration |
| `tests/tooling/` | Harnesses, judges, protocol, records, normative auditors and discovery | Their implementation, resources or consumers change; final integration |
| `tests/historical/` | Frozen cohort implementations and retained legacy simulations | Their dependencies change or an explicit audit; final integration |
| `support/` | Shared test mechanics, without a copied product implementation | Any consumer changes; independent extractor regressions retained |

These are deterministic tests of artifacts and tools. Behavioral experiments using
agents, models or Docker have separate hypotheses, inputs and outcomes; scenario
inputs remain in `scenarios/`. A green deterministic result does not establish
agent quality or cost savings.

## Commands

Run from the repository root. Each output directory must be new.

```sh
# Default: every registered family. This is also the unchanged CI command.
python3 eval/run_suites.py --output /tmp/tackle-full-results

# Explain affected families; no tests execute.
python3 eval/run_suites.py --changed eval/support/lint.py --dry-run --output /tmp/tackle-plan

# Execute the same affected families. Repeat --changed for every changed path.
python3 eval/run_suites.py --changed eval/support/lint.py --output /tmp/tackle-affected

# Final integration always executes the full registry, even with --changed.
python3 eval/run_suites.py --phase integration --output /tmp/tackle-integration
```

Supply both old and new paths for a rename, and the complete set of additions,
modifications and deletions. The runner does not infer an unstaged diff or run a
single method. Changing a registered test selects its whole family and discovery
regressions. Changing a producer selects its known consumers, including historical
cohorts where applicable. Unknown dependencies select the full registry. The map
in `check-selection.json` is conservative; it does not prove minimal selection.

Discovery validates **all** registered files before filtering execution. Missing,
unregistered or duplicate files reject a partial run too. Native count mismatches,
skips and child failures remain failures. Results retain commands, raw streams,
hashes, reasons, selected families and registered counts. `passed: true` with
`complete: false` approves only the selected families. A dry-run or empty affected
set records `passed: null` and zero executed tests.

Run affected families during a change. Run the full registry once on the final
integrated tree; rerun an affected check after its inputs change. Integration and
release phases always select every family. Release also retains all existing
requirements in [MAINTAINING.md](../MAINTAINING.md); selection adds no exemptions.
CI remains full on push and pull request.

## Maintaining coverage

Before adding a test, identify its guarantee, concrete failure, consumer and valid
alternative. Inspect existing cases and shared helpers. Expand or parameterize an
existing matrix when it can observe the new failure; create another method when
it protects a distinct guarantee. Avoid assertions that merely repeat the
implementation, and give tests names that match their actual oracle.

Trace the function, extracted recipe or artifact that each assertion actually
observes. A test-local implementation is a simulation, even when its output
resembles the product. Keep retained legacy simulations under `historical/`;
current migration tests execute the shipped recipes. A text-presence check
protects wording or structure, not an agent's obedience to it. An in-memory
checkpoint check does not demonstrate disk rollback.

For a weak oracle, use a concrete fault witness and a valid alternative within
its declared scope. Reuse the assertion used on the real consumer so a planted
defect must fail it; merely confirming that a deliberately broken helper produced
bad output is insufficient. Do not turn this into an exhaustive mutation quota.
Record what was reviewed statically, what was executed and what remains unproved.

When consolidating, preserve the input cases, fixtures, failure discrimination,
positive alternatives and consumers. Identical bodies alone do not establish
redundancy: historical cohorts exercise different sealed implementations. Their
tests remain separate; decision code, prices and synthetic fixtures stay intact.
The shared lint helper extracts the shipped recipe, while independent extractor
checks and differences in command delimiters and AWK variants remain covered.

Register every new/moved test file and update native counts. Review cross-family
edges in `check-selection.json` when adding a consumer or changing a loader; a
known producer must not silently omit a consumer. Use full execution when an edge
is uncertain. A registry/family change rejects a stale selective map. Keep plan
provenance out of distributed documentation and installation artifacts.
