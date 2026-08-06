# tracecheck — **Methodology: Tackle 5.0.2**

## Objective
A small trace utility for plan workspaces: prints the criterion↔point coverage matrix for a plan.

## 5. Point decomposition

| Point | What | Briefing | Depends on |
|---|---|---|---|
| **P-tc-core** | Matrix engine — parse §6 criteria and point anchors; emit one row per criterion | `points/P-tc-core.md` | none |
| **P-tc-report** | Report writer — append the matrix and the findings digest to `log.md` | `points/P-tc-report.md` | P-tc-core |

## 6. Acceptance criteria

### 6.1 Coverage matrix
The trace output prints exactly one row per acceptance criterion in §6, with a `covered`/`gap` status per row.

### 6.2 Point accounting
Every point id listed in §5 appears in the trace output.

## Non-goals
- No web UI; no changes to the workspace files beyond the `log.md` evidence block.
