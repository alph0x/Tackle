# Log — mini

**Append-only** log, ascending chronological order (newest at the bottom). One entry per
session: `## YYYY-MM-DD · session N · <title>` with **Did / Decisions / Blockers / Next** and,
at the end of the **newest** entry, a **State snapshot** sufficient to resume without
re-reading history. Keep entries terse (append-only ≠ verbose). Never rewrite old entries.
**This is the canonical state source of the plan.**

**Evidence entries** — every "done-signal passed/failed" claim carries:

````
**Evidence** — `the literal command`
```
trimmed output (≤ 10 lines, keep counts/exit line)
```
exit: 0
````

No evidence block ⇒ the claim is an assertion, and the point may not flip 🟢.

---

## 2026-08-21 · session 1 · P-01 implemented

### Did
- Added the hello line to `src/a.py`.
- Ran the done-signal; it passed (evidence below).

### Evidence
**Evidence** — `grep -q hello src/a.py`
```
(no output — match found, grep exits 0)
```
exit: 0

### Next
- Close point P-01: flip the board per the closure protocol.

### State snapshot
- Done: P-01 implemented, done-signal passed (evidence above).
- In flight: P-01 close pending.
- Blocked on: nothing.
- Resume from: close P-01.
