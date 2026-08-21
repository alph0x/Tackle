# Quality-dimensions catalog

Each fired axis becomes a runnable done-signal fragment folded into the point's Acceptance, or a review-gated criterion only if no honest command exists. An axis fires when the point's **Touches** match its heuristic; omit axes that don't fire.

| Axis | Fires when (Touches heuristic) | Done-signal fragment (example shape) | If no honest command |
|---|---|---|---|
| Security | Touches auth, input validation, secrets, or a trust boundary. | Test asserts unauthenticated/cross-tenant access → 401/403; grep confirms no secret literals in the diff. | Review-gate: security checklist filled and reviewed. |
| Performance | Touches a hot path, large-N structure, or tight loop. | Timing assertion under a hard budget (e.g. fixture run completes < N ms). | Review-gate: Big-O reasoning recorded and reviewed. |
| Concurrency | Touches parallelism, async flows, locks, or shared mutable state. | Suite repeats ×N under a hard timeout; race checker clean if the environment has one. | Review-gate: lock-ordering / async-safety walkthrough. |
| Correctness | Every point — fires by default. | The done-signal itself: tests over the case set, count-asserted where the set is finite. | Review-gate: worked examples reviewed against the spec. |
| Test depth | Every code point; escalates with risk — acceptance on public-behavior changes, property on parsers/transforms/money, fuzz on untrusted input/concurrency, mutation on money/security invariants. | Each fired tier folded as a runnable fragment — e.g. property runner ≥ N cases with recorded seed; one deliberate break → done-signal fails. | Review-gate: tier ladder reviewed with the reason each non-fired tier doesn't fire. |
| Data integrity | Touches persistence, migrations, serialization, or schemas. | Round-trip test (write → read → compare); migration up + down leaves data intact. | Review-gate: migration plan reviewed with a rollback path. |
| Accessibility (a11y) | Touches UI, markup, or user-facing flows. | Automated a11y linter passes; labels/roles asserted in component tests. | Review-gate: manual checklist (contrast, focus order, screen reader). |
| Internationalization (i18n) | Touches user-visible strings, dates, numbers, or currencies. | grep finds no hardcoded user-facing literals outside the string catalog. | Review-gate: locale walkthrough on the changed screens. |
| Observability | Touches error handling, external calls, or long-running jobs. | Test asserts the failure path emits the expected log/metric/event. | Review-gate: runbook entry reviewed (what to look at when it breaks). |
| Resilience | Touches retries, timeouts, external dependencies, or failure paths. | Test injects the dependency failure and asserts graceful degradation or retry. | Review-gate: failure-mode table reviewed. |

**A checklist is grounded or it is noise.** A quality checklist for a point names that point's actual surface: the changed files, the done-signal command, the Touches, and the axes whose heuristic fires. A generic boilerplate list (style, docs, "add tests") that any change could pass is a rubber stamp — it checks nothing this change actually did.
