# portable — **Methodology: Tackle 5.0.2**

## Objective
Refactor the `portable` CLI so config loading, output formatting, and docs are separated into stable modules.

## 5. Point decomposition

| Point | What | Briefing | Depends on |
|---|---|---|---|
| **P-port-config** | Extract config loading into `src/config.py` | `points/P-port-config.md` | none |
| **P-port-output** | Extract output formatting into `src/output.py` | `points/P-port-output.md` | P-port-config |
| **P-port-docs** | Update README and usage text | `points/P-port-docs.md` | P-port-output |

## 6. Acceptance criteria

### 6.1
`python3 -m py_compile src/*.py` passes.

### 6.2
`portable --help` shows the new usage text.

## Non-goals
- No new features; no packaging changes.
