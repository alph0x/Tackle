# Reference — current code state

**Current** state of the relevant code, grounded in `file:line`. Verify against the repo
before asserting (use your code-search / find-references tools, not memory). Don't infer.

## {{Component / layer}}

- `{{path/File.swift:NN}}` — {{what it does today}}.
- {{...}}

## Current types / contracts

- `{{Type}}` (`{{path:NN}}`): {{fields / relevant semantics}}.

## Verified chains / flows
<!-- Delete if not applicable. Document real paths with file:line, not invented diagrams. -->

```
{{A → B → C}}  ({{path:NN}})
```

## Quality tooling (how each fired dimension gets verified here)
<!-- Discovered in the Step 5 quality-dimensions pass. Per-point done-signal fragments map to
     these. Note a MISSING mechanism explicitly — that absence is a finding, not a blank.
     Delete rows no point in this initiative fires. -->

- **Tests**: {{runner + invocation — e.g. `npm test`, `swift test --filter <Suite>`}}.
- **Lint / format / style**: {{linter/formatter + how to run it; the self-documenting check}}.
- **Concurrency**: {{strict-mode/race flag or detector — e.g. `-strict-concurrency=complete`, `-race`; or "none — flag"}}.
- **Security**: {{secret-scan / SAST / authz-test harness; or "none — flag"}}.
- **Performance**: {{bench harness + how a threshold is asserted; or "none — flag"}}.
- **CI gates**: {{what CI enforces on a PR}}.
