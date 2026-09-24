# Quality-dimensions catalog

Each fired axis becomes a runnable acceptance check fragment folded into the Task's Acceptance, or a
review-gated criterion only if no honest command exists. An axis fires when the Task's Write scope
match its heuristic; omit axes that do not fire. Quality asks whether the implementation owns a
coherent observable responsibility and satisfies constraints relevant to its consumers.

| Axis | Fires when (Write scope heuristic) | Acceptance check fragment (example shape) | If no honest command |
|---|---|---|---|
| Security | Write scope includes auth, input validation, secrets, or a trust boundary. | Test asserts unauthenticated/cross-tenant access → 401/403; grep confirms no secret literals in the diff. | Review-gate: security checklist filled and reviewed. |
| Performance | Write scope includes a hot path, large-N structure, or tight loop. | Timing assertion under a hard budget (e.g. fixture run completes < N ms). | Review-gate: Big-O reasoning recorded and reviewed. |
| Concurrency | Write scope includes parallelism, async flows, locks, or shared mutable state. | Suite repeats ×N under a hard timeout; race checker clean if the environment has one. | Review-gate: lock-ordering / async-safety walkthrough. |
| Correctness | Every task — fires by default. | The acceptance check itself: tests over the complete case set, count-asserted where the set is finite, with required outputs and invalid cases. | Review-gate: worked examples reviewed against the spec. |
| Test depth | Every code task considers an E2E check through its real consumer first; complex integrated features require one when feasible. Isolation fires only for a distinct uncovered failure mode documented before code (`references/guides/testing.md`). | The selected check covers contract cases; E2E emits a replayable artifact. Property/fuzz/mutation add only distinct risk coverage, preferably through the consumer. | Review-gate: reason E2E cannot cover an obligation and inventory isolated failure modes before implementation. |
| Data integrity | Write scope includes persistence, migrations, serialization, or schemas. | Round-trip test (write → read → compare); migration up + down leaves data intact. | Review-gate: migration plan reviewed with a rollback path. |
| Accessibility (a11y) | Write scope includes UI, markup, or user-facing flows. | Automated a11y linter passes; labels/roles asserted in component tests. | Review-gate: manual checklist (contrast, focus order, screen reader). |
| Internationalization (i18n) | Write scope includes user-visible strings, dates, numbers, or currencies. | grep finds no hardcoded user-facing literals outside the string catalog. | Review-gate: locale walkthrough on the changed screens. |
| Observability | Write scope includes error handling, external calls, or long-running jobs. | Test asserts the failure path emits the expected log/metric/event. | Review-gate: runbook entry reviewed (what to look at when it breaks). |
| Resilience | Write scope includes retries, timeouts, external dependencies, or failure paths. | Test injects the dependency failure and asserts graceful degradation or retry. | Review-gate: failure-mode table reviewed. |

Initiative-wide axes live in `plan.md` §6.1.
