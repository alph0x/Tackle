# Action plan — mini

## 1. Objective

Add a hello check to `src/a.py`.

## 5. Point decomposition

| Point | What | Briefing | Depends on |
|---|---|---|---|
| **P-01 · hello check** | ensure `src/a.py` answers hello | `points/P-01.md` | none |

### Dependency graph

```
P-01   (single point)
```

## 6. Acceptance criteria

### 6.1 Universal per-point acceptance
- [ ] The done-signal is a literal command with a pass condition.
- [ ] Board hygiene: `board.md` + `log.md` updated.

### 6.2 Initiative-level acceptance
- [ ] `grep -q hello src/a.py` exits 0.
