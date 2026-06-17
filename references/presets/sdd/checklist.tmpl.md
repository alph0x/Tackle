---
initiative: {{INITIATIVE_NAME}}
created: {{DATE}}
source: {{SOURCE_PATH}}
---

# Quality checklist — {{INITIATIVE_NAME}}

## How to use this checklist

This checklist is derived from `{{SOURCE_PATH}}`. Read the source artifact first, then walk the five quality dimensions below. Skip any dimension the source does not fire, and record the reason under **Why skipped** in that section. Each fired axis must become either a concrete review prompt or a runnable done-signal fragment. Do not leave generic prose as a substitute for a check.

## Quality dimensions

### Security

Framing: every trust boundary, external input, secret, path, query, and cryptographic operation in `{{SOURCE_PATH}}` must have a verifiable control.

- [ ] For every route / endpoint / public function in `{{SOURCE_PATH}}` §API, is there an authz test that asserts unauthenticated → 401 / unauthorized → 403?
- [ ] Does every user-supplied value pass through validation before it reaches business logic or a query builder?
- [ ] Are secrets (tokens, keys, passwords) loaded from environment / a secrets manager, never committed or logged?
- [ ] Are file paths / identifiers scoped to the authenticated principal (no path traversal / insecure direct object reference)?
- [ ] Is cryptography limited to approved algorithms and libraries recorded in `reference.md`?

Tooling / runnable fragment:

```bash
# example: adjust to the repo's test runner
{{SECURITY_RUNNABLE}}
```

Why skipped: {{SECURITY_SKIP_REASON}}

### Performance

Framing: hot paths, loops over data size N, I/O inside requests, and allocation in tight loops must be bounded or measured.

- [ ] For every loop or batch operation in `{{SOURCE_PATH}}`, is its cost stated in terms of N and bounded by the acceptance criteria?
- [ ] Does any path make I/O (network, disk, DB) inside a user-facing request? If so, is it async, batched, or justified?
- [ ] Are tight loops free of allocations that scale with N?
- [ ] Is there a benchmark or latency target for the hot path named in `{{SOURCE_PATH}}`?

Tooling / runnable fragment:

```bash
# example: adjust to the repo's benchmark / profiler
{{PERFORMANCE_RUNNABLE}}
```

Why skipped: {{PERFORMANCE_SKIP_REASON}}

### Concurrency

Framing: shared mutable state, async flow, parallel access, and locking must be explicit and race-free.

- [ ] Does any mutable state cross an async / thread boundary? If yes, is access synchronized or made immutable?
- [ ] Are there locks with a documented ordering and a timeout / deadlock guard?
- [ ] Does `{{SOURCE_PATH}}` describe parallel agents or subagents? If so, are their `Depends-on` + `Touches` constraints enough to prevent collisions?
- [ ] Has the code been run under the repo's race / thread-sanitizer flag?

Tooling / runnable fragment:

```bash
# example: adjust to the repo's concurrency checker
{{CONCURRENCY_RUNNABLE}}
```

Why skipped: {{CONCURRENCY_SKIP_REASON}}

### Correctness

Framing: finite case-sets, boundary / edge inputs, and error states must be enumerated and checked.

- [ ] For every conditional or state machine in `{{SOURCE_PATH}}`, are the branches enumerated in the acceptance criteria or tests?
- [ ] Are boundary inputs (empty, max, nil, overflow, timeout) listed with expected behavior?
- [ ] Does every error path return a usable error shape and leave the system in a safe state?
- [ ] Is the done-signal in `{{SOURCE_PATH}}` a runnable command or an explicit review gate with a rubric?

Tooling / runnable fragment:

```bash
# example: adjust to the repo's test suite
{{CORRECTNESS_RUNNABLE}}
```

Why skipped: {{CORRECTNESS_SKIP_REASON}}

### Conventions & Style

Framing: the codebase's linter, formatter, naming, and self-documenting-code rules are the always-on backbone.

- [ ] Does the plan's text follow the language convention in `SKILL.md` (English for workspace artifacts)?
- [ ] Does every `file:line` citation in `{{SOURCE_PATH}}` resolve to real code?
- [ ] Are there no inline comments explaining *what* the plan says; intent and non-obvious tradeoffs only?
- [ ] Does the artifact pass the repo's formatter / linter without overrides?

Tooling / runnable fragment:

```bash
# example: adjust to the repo's lint / format command
{{CONVENTIONS_RUNNABLE}}
```

Why skipped: {{CONVENTIONS_SKIP_REASON}}

## Degraded source path

If `{{SOURCE_PATH}}` does not exist when `/tackle-checklist` is invoked, produce a degraded `checklist.md` that lists the five dimensions above and asks the user to point to a `spec.md` or `plan.md` under `docs/plans/{{INITIATIVE_NAME}}/`. Do not fail silently.
