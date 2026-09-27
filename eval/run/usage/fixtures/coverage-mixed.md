# Coverage fixture — mixed role/session scope

## Lifecycle input

| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-04-sm/P-03/Driver/01 | start | P-03 | Driver | openai-responses | standard | gpt-5 | medium | 2026-09-04T10:00:00Z | running | n/a | n/a | n/a | agent-observed |
| 2026-09-04-sm/P-03/Driver/01 | finish | P-03 | Driver | openai-responses | standard | gpt-5 | medium | 2026-09-04T10:04:00Z | success | 1 | 0 | passed | agent-observed |

## Coverage input

| Metric | Scope | Measured | Eligible | Result |
|---|---|---:|---:|---|
| tokens | role | 1 | 2 | 1/2 (50%) |
| tokens | session | 1 | 1 | 1/1 (100%) |

Exact role observation: `input_tokens=90`, `output_tokens=30`. Session observation is `scope_id=session-7` and cannot map exactly to the role. Expected: keep scopes separate, suppress cross-scope totals/rankings/recommendations.
