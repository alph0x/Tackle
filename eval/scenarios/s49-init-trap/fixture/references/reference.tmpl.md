# Reference — current code state

**Current** state of the relevant code, grounded in anchored citations —
`file:NN — "literal fragment"`, fragment = verbatim substring of line NN. Verify against the repo
before asserting (use your code-search / find-references tools, not memory). Don't infer.

## {{Component / layer}}
Last-verified: {{YYYY-MM-DD}}

- `{{path/File.swift:NN}} — "{{literal fragment}}"` — {{what it does today}}.
- {{...}}

## Current types / contracts
Last-verified: {{YYYY-MM-DD}}

- `{{Type}}` (`{{path:NN}} — "{{literal fragment}}"`): {{fields / relevant semantics}}.

## Verified chains / flows
Last-verified: {{YYYY-MM-DD}}
<!-- Delete if not applicable. Document real paths with file:line, not invented diagrams. -->

```
{{A → B → C}}  ({{path:NN}})
```

## Quality tooling (how each fired dimension gets verified here)
Last-verified: {{YYYY-MM-DD}}
<!-- Discovered in the Step 5 quality-dimensions pass. Per-point done-signal fragments map to
     these. Note a MISSING mechanism explicitly — that absence is a finding, not a blank.
     Delete rows no point in this initiative fires. -->

- **Tests**: {{runner + invocation — e.g. `npm test`, `swift test --filter <Suite>`}}.
- **Lint / format / style**: {{linter/formatter + how to run it; the self-documenting check}}.
- **Concurrency**: {{strict-mode/race flag or detector — e.g. `-strict-concurrency=complete`, `-race`; or "none — flag"}}.
- **Security**: {{secret-scan / SAST / authz-test harness; or "none — flag"}}.
- **Performance**: {{bench harness + how a threshold is asserted; or "none — flag"}}.
- **CI gates**: {{what CI enforces on a PR}}.
