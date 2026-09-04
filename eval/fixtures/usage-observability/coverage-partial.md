# Coverage fixture — partial exact telemetry

## Lifecycle input

| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-04-sp/P-03/Driver/01 | start | P-03 | Driver | claude-code | standard | claude-sonnet | medium | 2026-09-04T10:00:00Z | running | n/a | n/a | n/a | agent-observed |
| 2026-09-04-sp/P-03/Driver/01 | finish | P-03 | Driver | claude-code | standard | claude-sonnet | medium | 2026-09-04T10:04:00Z | success | 1 | 0 | passed | agent-observed |
| 2026-09-04-sp/P-03/Driver/02 | start | P-03 | Driver | claude-code | standard | claude-sonnet | medium | 2026-09-04T10:05:00Z | running | n/a | n/a | n/a | agent-observed |
| 2026-09-04-sp/P-03/Driver/02 | finish | P-03 | Driver | claude-code | standard | claude-sonnet | medium | 2026-09-04T10:09:00Z | success | 2 | 1 | passed | agent-observed |

## Coverage input

| Metric | Scope | Measured | Eligible | Result |
|---|---|---:|---:|---|
| tokens | role | 1 | 2 | 1/2 (50%) |
| duration | role | 2 | 2 | 2/2 (100%) |

Exact observation: `input_tokens=120`, `output_tokens=40`, role-scoped. Expected: list the labeled observation, suppress cohort totals/rankings and tier/effort recommendations because token coverage is partial.
