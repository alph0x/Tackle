---
initiative: {{INITIATIVE_NAME}}
created: {{DATE}}
source: {{SOURCE_PATH}}
---

# Quality checklist — {{INITIATIVE_NAME}}

Read `{{SOURCE_PATH}}` first. Walk the six dimensions below; skip dimensions the source does not fire and record why. Each fired dimension becomes concrete review prompts or a runnable done-signal fragment.

## Security

Check every trust boundary, external input, secret, path, query, and crypto op in `{{SOURCE_PATH}}`.

- [ ] Every route / endpoint / public function has an authz test for 401/403.
- [ ] Every user-supplied value is validated before business logic / query builder.
- [ ] Secrets load from environment / secrets manager, never committed or logged.
- [ ] Paths / identifiers are scoped to the authenticated principal (no traversal / IDOR).
- [ ] Crypto uses approved algorithms and libraries recorded in `reference.md`.

```bash
# adjust to the repo's test runner
{{SECURITY_RUNNABLE}}
```

Why skipped: {{SECURITY_SKIP_REASON}}

## Performance

Check hot paths, loops over N, I/O inside requests, and allocations in tight loops.

- [ ] Every loop / batch cost is stated in terms of N and bounded by acceptance criteria.
- [ ] I/O inside user-facing requests is async, batched, or justified.
- [ ] Tight loops don't allocate in proportion to N.
- [ ] Hot path has a benchmark or latency target.

```bash
# adjust to the repo's benchmark / profiler
{{PERFORMANCE_RUNNABLE}}
```

Why skipped: {{PERFORMANCE_SKIP_REASON}}

## Concurrency

Check shared mutable state, async flow, parallel access, and locking.

- [ ] Mutable state crossing async / thread boundaries is synchronized or immutable.
- [ ] Locks have documented ordering and a timeout / deadlock guard.
- [ ] Parallel agents / subagents have `Depends-on` + `Touches` constraints that prevent collisions.
- [ ] Code has been run under the repo's race / thread-sanitizer flag.

```bash
# adjust to the repo's concurrency checker
{{CONCURRENCY_RUNNABLE}}
```

Why skipped: {{CONCURRENCY_SKIP_REASON}}

## Observability

Check that production paths are debuggable and their failure modes are visible.

+- [ ] Every new production path logs enough context to debug failures without guessing.
+- [ ] Key metrics exist for throughput, errors, and latency on user-facing or critical paths.
+- [ ] Alerts fire on symptoms (not just causes) for failure modes that affect users or SLOs.
+- [ ] A runbook or rollback path exists for critical failure modes.

```bash
# adjust to the repo's observability validation (logs / metrics / traces)
{{OBSERVABILITY_RUNNABLE}}
```

Why skipped: {{OBSERVABILITY_SKIP_REASON}}

## Correctness

Check finite case-sets, boundary inputs, and error states.

- [ ] Branches of every conditional / state machine are enumerated in acceptance criteria or tests.
- [ ] Boundary inputs (empty, max, nil, overflow, timeout) have expected behavior listed.
- [ ] Every error path returns a usable error shape and leaves the system safe.
- [ ] Done-signal is a runnable command or an explicit review gate with a rubric.

```bash
# adjust to the repo's test suite
{{CORRECTNESS_RUNNABLE}}
```

Why skipped: {{CORRECTNESS_SKIP_REASON}}

## Conventions & Style

Check linter, formatter, naming, and self-documenting-code rules.

- [ ] Workspace artifacts follow the language convention in `SKILL.md`.
- [ ] Every `file:line` citation in `{{SOURCE_PATH}}` resolves to real code.
- [ ] No inline comments explaining *what*; intent and non-obvious tradeoffs only.
- [ ] Artifact passes the repo's formatter / linter without overrides.

```bash
# adjust to the repo's lint / format command
{{CONVENTIONS_RUNNABLE}}
```

## Degraded source path

If `{{SOURCE_PATH}}` does not exist, list the six dimensions above and ask the user to point to a `spec.md` or `plan.md` under `docs/plans/{{INITIATIVE_NAME}}/`. Do not fail silently.
