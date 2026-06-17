# Log — {{TITLE}}

**Append-only** log, ascending chronological order (newest at the bottom). One entry per
session: `## YYYY-MM-DD · session N · <title>` with **Did / Decisions / Blockers / Next** and,
at the end of the **newest** entry, a **State snapshot** sufficient to resume without
re-reading history. Keep entries terse (append-only ≠ verbose). Never rewrite old entries.
Never log secrets. **This is the canonical state source of the plan.**

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

### Next
- {{...}}

### State snapshot (keep current in the newest entry only)
- Done: {{what's settled / which points are ready}}
- In flight: {{active point P-0x, where it stands}}
- Blocked on: {{Q-0x / external}}
- Resume from: {{the one concrete next action}}
