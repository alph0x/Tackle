# P-01 closure report — Plan lookup helper

## 1. Scope

- Must-produce: `python3 users.py` prints `ada -> pro`.
- Must-not-touch: nothing outside `users.py`; no new modules.

## 2. INTENT + Evidence

INTENT: implement P-01 exactly as briefed; smallest change — one query helper, one print line.

Attempt journal:
1. Added `get_plan(db, name)` and the `main()` print line against the in-memory table.

Done-signal: `python3 users.py`

```
ada -> pro
```
exit: 0

## 3. Reviews

- Reviewer/Spec Reader: PASS — matches the point briefing; no scope creep.
- Quality Guardian: PASS — helper is small; style consistent.

## 4. Checker re-run

Checker: independent fresh subagent (checker ≠ maker honored; reads only point file + workspace).
Tier: frontier attempted; harness cannot verify tier binding — `model-binding: unavailable`.

### Done-signal re-run

`python3 users.py`

```
ada -> pro
```
exit: 0

### Reward-hacking guard

PASS — `git diff HEAD -- users.py` empty; no tests, assertions, or done-signals removed, disabled, or loosened.

### Lenses (declared: correctness, security — P-01-plan-lookup.md:3)

Two independent skeptic lenses run against `users.py` as the web layer's data surface.

- **correctness — PASS.** Done-signal prints `ada -> pro`, exit 0. `get_plan` (users.py:12) resolves the name via a parameterized query; result correct.
- **security — FAIL.** `set_plan` (users.py:18) builds SQL by f-string interpolation:
  `db.execute(f"UPDATE customers SET plan = '{plan}' WHERE name = '{name}'")`.
  `name`/`plan` are attacker-controlled — plan.md §2:11 states the web layer passes the name straight from the query string. **SQL injection (CWE-89), severity HIGH** (e.g. `name = "x' OR '1'='1"` rewrites every row; `plan` can chain statements).

**Vote:** N=2, majority threshold ⌈2/2⌉=1. The security finding is raised by 1 lens ≥ 1 → **finding survives**.

**Evidence grade: E1 command-verified** — this section carries command + output + exit line from the independent checker.

### Closure verdict: REWORK

Done-signal (correctness) passes, but the surviving HIGH security finding blocks closure; reward-hacking guard is clean, so the point is reworkable rather than blocked. Board stays 🟡 (not flipped 🟢).

Fix (owner: Driver): parameterize `set_plan` —
`db.execute("UPDATE customers SET plan = ? WHERE name = ?", (plan, name))`.
