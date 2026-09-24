# Log — portable

**Append-only** log, ascending chronological order (newest at the bottom). One entry per session: `## YYYY-MM-DD · session N · <title>` with **Did / Decisions / Blockers / Next** and, at the end of the **newest** entry, a **State snapshot** sufficient to resume without re-reading history. **This is the canonical state source of the plan.**

---

## 2026-08-04 · session 2 · output extraction

### Did
- Extracted config loading into `src/config.py` (P-port-config done; `python3 -m py_compile src/config.py src/main.py` green).
- Started P-port-output: formatter skeleton in `src/output.py`; plain-text path done.

### Decisions
- D-02 confirmed: formatter covers plain-text, JSON, and table; no CSV path this round.

### Blockers / open questions
- Q-02: color output default for TTYs — on or off? Owner: user.

### Next
- Finish P-port-output (JSON + table paths), then P-port-docs.

### State snapshot (keep current in the newest entry only)
- Done: P-port-config.
- In flight: P-port-output (plain-text done; JSON + table pending).
- Blocked on: nothing.
- Resume from: P-port-output — JSON path in `src/output.py`.

---

## 2026-08-03 · session 1 · kickoff

### Did
- Plan scaffolded; three points briefed; D-01 (config module name) recorded.

### Decisions
- D-01: config loading lives in `src/config.py` (not `src/settings.py`).

### Next
- Extract config (P-port-config).
