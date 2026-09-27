# Lifecycle fixture — planted invalid runs

The validator must print every id below; the fixture intentionally contains multiple defects.

| Run ID | Event | Point | Role | Harness | Tier | Model | Effort | At | Outcome | Attempts | Rework | Verification | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| invalid/duplicate-start | start | P-05 | Driver | generic | standard | n/a | medium | 2026-09-04T11:00:00Z | running | n/a | n/a | n/a | agent-observed |
| invalid/duplicate-start | start | P-05 | Driver | generic | standard | n/a | medium | 2026-09-04T11:01:00Z | running | n/a | n/a | n/a | agent-observed |
| invalid/duplicate-start | finish | P-05 | Driver | generic | standard | n/a | medium | 2026-09-04T11:02:00Z | success | 1 | 0 | passed | agent-observed |
| invalid/orphan-terminal | finish | P-05 | Driver | generic | standard | n/a | medium | 2026-09-04T11:02:00Z | success | 1 | 0 | passed | agent-observed |
| invalid/duplicate-terminal | start | P-05 | Driver | generic | standard | n/a | medium | 2026-09-04T11:00:00Z | running | n/a | n/a | n/a | agent-observed |
| invalid/duplicate-terminal | finish | P-05 | Driver | generic | standard | n/a | medium | 2026-09-04T11:01:00Z | success | 1 | 0 | passed | agent-observed |
| invalid/duplicate-terminal | observe-incomplete | P-05 | Driver | generic | standard | n/a | medium | 2026-09-04T11:02:00Z | incomplete | n/a | n/a | n/a | coordinator-observed |
| invalid/negative-count | start | P-05 | Driver | generic | standard | n/a | medium | 2026-09-04T11:00:00Z | running | n/a | n/a | n/a | agent-observed |
| invalid/negative-count | finish | P-05 | Driver | generic | standard | n/a | medium | 2026-09-04T11:01:00Z | success | -1 | 0 | passed | agent-observed |
| invalid/mismatched-identity | start | P-05 | Driver | generic | standard | n/a | medium | 2026-09-04T11:00:00Z | running | n/a | n/a | n/a | agent-observed |
| invalid/mismatched-identity | finish | P-06 | Driver | generic | standard | n/a | medium | 2026-09-04T11:01:00Z | success | 1 | 0 | passed | agent-observed |
