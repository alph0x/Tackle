# Coverage fixture — full comparable telemetry

## Lifecycle input

| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-04-sf/P-03/Driver/01 | start | P-03 | Driver | claude-code | standard | claude-sonnet | medium | 2026-09-04T10:00:00Z | running | n/a | n/a | n/a | agent-observed |
| 2026-09-04-sf/P-03/Driver/01 | finish | P-03 | Driver | claude-code | standard | claude-sonnet | medium | 2026-09-04T10:04:00Z | success | 1 | 0 | passed | agent-observed |
| 2026-09-04-sf/P-03/Driver/02 | start | P-03 | Driver | claude-code | standard | claude-sonnet | medium | 2026-09-04T10:05:00Z | running | n/a | n/a | n/a | agent-observed |
| 2026-09-04-sf/P-03/Driver/02 | finish | P-03 | Driver | claude-code | standard | claude-sonnet | medium | 2026-09-04T10:09:00Z | success | 2 | 1 | passed | agent-observed |
| 2026-09-04-sf/P-03/Driver/03 | start | P-03 | Driver | claude-code | standard | claude-sonnet | medium | 2026-09-04T10:10:00Z | running | n/a | n/a | n/a | agent-observed |
| 2026-09-04-sf/P-03/Driver/03 | finish | P-03 | Driver | claude-code | standard | claude-sonnet | medium | 2026-09-04T10:14:00Z | success | 1 | 0 | passed | agent-observed |

## Coverage input

| Metric | Scope | Measured | Eligible | Result |
|---|---|---:|---:|---|
| tokens | role | 3 | 3 | 3/3 (100%) |
| duration | role | 3 | 3 | 3/3 (100%) |

Exact observations: `input_tokens=120, output_tokens=40`; `input_tokens=140, output_tokens=50`; `input_tokens=160, output_tokens=60`. Expected totals: input 420, output 150. Three identical-scope completed runs permit a labeled tier/effort recommendation.
