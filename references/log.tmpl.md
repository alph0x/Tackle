# Log — {{TITLE}}

**Append-only** log, ascending chronological order (newest at the bottom). One entry per
session: `## YYYY-MM-DD · session N · <title>` with **Did / Decisions / Blockers / Next** and,
at the end of the **newest** entry, a **State snapshot** sufficient to resume without
re-reading history. Keep entries terse (append-only ≠ verbose). Never rewrite old entries.
Never log secrets. **This is the canonical state source of the plan.**

**Archive protocol** — when `log.md` exceeds ~400 lines, move entries older than the
last 5 sessions **verbatim** to `log-archive.md`. Append-only is preserved across the pair:
never edit moved entries. The newest entry always keeps a self-sufficient State snapshot,
so archiving never breaks resume. Thresholds are workspace-overridable in `AGENTS.md`.

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

## {{YYYY-MM-DD}} · session 1 · plan kickoff

### Intake (context gathered)
- Requirement: {{the ask in the user's words / ticket}}
- Docs read: {{links, files}}
- Scope hints / decision owners: {{...}}
- Codebase: {{repo path}}

### Did
- {{...}}

### Decisions
- {{D-0x: one-liner — full entry recorded in `decisions.md`}}

### Blockers / open questions
- {{see `questions.md`: Q-01, ...}}
<!-- Failed attempts: one journal line per attempt, each with its evidence block:
attempt N: <what was tried> — failed because <lesson>
On budget exhaustion or no-progress (two consecutive attempts with identical evidence
output), the point flips ⏸ and the entry carries the escalation packet:
### Escalation — P-NN
- Attempts: N (budget M) · reason: budget | no-progress
- Attempt journal: the per-attempt lines above (with evidence blocks, last attempt at minimum)
- Hypothesis: the current best explanation of the failure
- Unblocking question: the smallest question that would unblock → Q-xx (user-owned if applicable)
-->


### Next
- {{...}}

### State snapshot (keep current in the newest entry only)
- Done: {{what's settled / which points are ready}}
- In flight: {{active point P-0x, where it stands}}
- Blocked on: {{Q-0x / external}}
- Resume from: {{the one concrete next action}}
