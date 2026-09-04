# Coverage fixture — zero exact telemetry

## Lifecycle input

| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-04-sz/P-03/Driver/01 | start | P-03 | Driver | generic | standard | n/a | high | 2026-09-04T10:00:00Z | running | n/a | n/a | n/a | agent-observed |
| 2026-09-04-sz/P-03/Driver/01 | finish | P-03 | Driver | generic | standard | n/a | high | 2026-09-04T10:04:00Z | success | 1 | 0 | passed | agent-observed |
| 2026-09-04-sz/P-03/Checker/01 | start | P-03 | Checker | generic | frontier | n/a | high | 2026-09-04T10:01:00Z | running | n/a | n/a | n/a | agent-observed |
| 2026-09-04-sz/P-03/Checker/01 | observe-incomplete | P-03 | Checker | generic | frontier | n/a | high | 2026-09-04T10:05:00Z | incomplete | n/a | n/a | n/a | coordinator-observed |

## Coverage input

| Metric | Scope | Measured | Eligible | Result |
|---|---|---:|---:|---|
| tokens | role | 0 | 2 | 0/N (0%) |
| duration | role | 1 | 2 | 1/2 (50%) |

Expected: duration and incomplete counts remain usable; exact-token totals and recommendations are suppressed.
