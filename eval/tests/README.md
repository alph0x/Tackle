# Test suites by functionality

Use the feature directory to find what a suite verifies. Categories describe its
consumer; dates and experiment identifiers belong to evidence provenance.

| Category | Suite | Guarantees |
|---|---|---|
| historical | [historical/migration/copy-and-adoption](historical/migration/copy-and-adoption/) | Legacy copy-first/adoption examples implemented locally; not current migration recipes. |
| historical | [historical/verdicts/cost-and-fall-rate](historical/verdicts/cost-and-fall-rate/) | Cost medians, fall-rate bounds, tripwires and routed-planning recommendations. |
| historical | [historical/verdicts/escalation-and-completeness](historical/verdicts/escalation-and-completeness/) | Minimum sample counts, escalation model routing and report-only split summaries. |
| historical | [historical/verdicts/no-regression](historical/verdicts/no-regression/) | Non-regression verdicts, current-workspace comparisons and artifact ties. |
| historical | [historical/verdicts/resume-comparison](historical/verdicts/resume-comparison/) | Resume comparison, ordered records, cost summaries and report-only guarantees. |
| product | [product/install/inventory](product/install/inventory/) | Installed artifact inventory, links and root resolution. |
| product | [product/lessons](product/lessons/) | Learning confidence, coverage tables and retrospective identifiers. |
| product | [product/lint/rows](product/lint/rows/) | Canonical lint rows, formats, severities, AWK variants, lifecycle outcomes, clock coverage and Attempts evidence. |
| product | [product/lint/task-contracts](product/lint/task-contracts/) | Task contracts, readiness and acceptance fields. |
| product | [product/lint/task-identity](product/lint/task-identity/) | Task identity, scaffold paths and workspace naming. |
| product | [product/migration](product/migration/) | Workspace schema migration, recipes and census refusal. |
| product | [product/plan](product/plan/) | Plan section order, and the controlled-writing recipe and guide for owner texts and specifications. |
| product | [product/resume](product/resume/) | The cold-resume read order, its links from every read list, the spent-count source and the closure listing of open obligations. |
| product | [product/run/card](product/run/card/) | Execution state transitions, template bindings and adversary-checkpoint records. |
| product | [product/run/evidence-capture](product/run/evidence-capture/) | Child execution, streams, timeouts and evidence capture. |
| product | [product/run/execution](product/run/execution/) | Literal execution recipes, identity and verdict capture. |
| product | [product/run/focused-closure](product/run/focused-closure/) | Focused completion receipts and artifact hashing. |
| product | [product/run/usage](product/run/usage/) | Native usage-event capture and lifecycle accounting. |
| product | [product/run/verification-records](product/run/verification-records/) | Verification-record integrity, export, concurrency and maintenance. |
| product | [product/status](product/status/) | Context projections, archives, resume and handoff costs, the plan view and self-contained executive Plan/Progress/Both PDF export recipes, truthful canonical aggregates, print lifecycle and the architecture map. Optional curated presentation and complete canonical requirement and decision details through the actual shipped recipe. The page's own controller runs on its own markup in a minimal DOM: one reversible selection shared by the graph, the task list, the inspector, the title strip, the requirement list, anchors and the public API: a task traces its prerequisites and dependents, a requirement marks the tasks that cover it; filters, the persisted theme choice, readable-minimum diagram zoom, pinch and ctrl-wheel zoom around the pointer, a header index that stacks instead of clipping and the optional live client. Architecture arrows carry their recorded words, a complete source, relation and destination guide precedes selection, and a selected component narrows arrows and guide and opens a lens of what flows into it and out of it, where neighbors can be walked, until cleared. Static readers get the same facts: a stage list in the graph's columns, a title strip in board order, Spanish state names and a print palette equal to the light screen tokens. The local live producer refreshes declared public inputs within path, Host and freshness boundaries. Native browser layout, rendering and aesthetics remain outside these oracles. |
| product | [product/templates](product/templates/) | Template fields, observed model routing, capability recovery and compiled briefs. |
| tooling | [tooling/behavior/harness](tooling/behavior/harness/) | Agent adapters, usage parsing, broker isolation, harness commands, the subscription route (isolation, judging, records, loopback request parsing and interruption cleanup) and the JEV secondary signal (calibration, sidecar, key containment). |
| tooling | [tooling/behavior/judges/planning](tooling/behavior/judges/planning/) | Planning judgments, hidden acceptance boundaries and runner integrity. |
| tooling | [tooling/behavior/judges/resume](tooling/behavior/judges/resume/) | Resume ordering, migrated workspaces and portable verification records. |
| tooling | [tooling/install/reading-budget](tooling/install/reading-budget/) | Reading costs, load chains and duplication floors. |
| tooling | [tooling/maintaining/field-report](tooling/maintaining/field-report/) | Field-report aggregation, scope and malformed-input refusal. |
| tooling | [tooling/maintaining/suite-integrity](tooling/maintaining/suite-integrity/) | Complete discovery, conservative selection and credential guards. |
| tooling | [tooling/protocol-v2](tooling/protocol-v2/) | Evaluation protocol records and numerical verdict oracles. |
| tooling | [tooling/records](tooling/records/) | Record currency, pinned claims and publication sanitization. |
| tooling | [tooling/rules](tooling/rules/) | Normative inventory, ledger gates, committed-text leak scanning (including digest-keyed admission of sealed scenario trees) and removed-unit accounting. |
| tooling | [tooling/scenario-index](tooling/scenario-index/) | Scenario catalog consistency, variant registration and answer-sheet/oracle digests. |
| tooling | [tooling/validation-integrity](tooling/validation-integrity/) | Validation fields, dependency parsing and write-scope integrity. |

Historical verdict suites exercise distinct sealed implementations. Their source
directories retain archival identifiers for seal and evidence integrity; those
identifiers are not suite names. Synthetic cases and oracles remain independent.
The historical migration examples execute local simulation helpers. Product
migration tests separately execute the current shipped schema and step recipes.

See [TESTING.md](../TESTING.md) for selection, native results and consolidation.
[suite-manifest.json](../suite-manifest.json) maps every functional suite to its
implementation/fixtures and expected method count.
