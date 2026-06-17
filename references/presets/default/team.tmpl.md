# Team protocol — {{TITLE}}

When a point enters execution, the orchestrator spawns a **point team** sized to the point's complexity. The workspace (`board.md`, `log.md`, the point file, and the touched files) is the single source of truth; IRC is only for coordination.

## Team sizing

| Size | Roles | Use for |
|---|---|---|
| **Solo** | Driver only | Simple template creation, single-file additive changes, clear done-signal. |
| **Pair** | Driver + Reviewer | Routing changes, multi-file changes, or when a second pair of eyes reduces risk. |
| **Pod** | Driver + Spec Reader + Quality Guardian + Coordinator | Complex changes (execution engine, contract rewrite, architecture) or high-risk points. |
| **Squad** | Pod + Specialist(s) | Very complex or high-risk points (security, cross-cutting refactor, new subsystem). Add specialists as needed. |

Default: **Solo** unless the point briefing explicitly requests a larger team.

## Single source of truth for state

- **`board.md`** is the only place that records point status (🔴 🟡 ⏸ 🟢).
- **`log.md`** is append-only history. It records what happened, not the current state.
- **`todo.md`** is for planning-readiness; it is not updated during execution.
- **No IRC status payloads.** Coordination messages are plain prose; the board is where status lives.

## Roles (when used)

### Driver
- Owns the code changes. Writes files, runs tests, makes the done-signal pass.
- Writes the smallest change that makes the current verification green.
- Reports done-signal result and changed files.

### Reviewer (Pair mode)
- Owns spec alignment and quality in one role.
- Verifies the output matches the point briefing and `design-contract.md`.
- Reviews for Clean Code, SOLID, conventions, and markdown quality.
- Reports PASS or findings.

### Spec Reader (Pod/Squad mode)
- Owns alignment with the point briefing and `design-contract.md`.
- Summarizes must-produce / must-not-touch before the Driver writes.
- Verifies output after the Driver reports done.

### Quality Guardian (Pod/Squad mode)
- Owns code quality, conventions, and Tackle best practices.
- Reviews each diff for smells, redundancy, SOLID, naming, and self-documenting code.

### Coordinator (Pod/Squad mode)
- Owns flow and workspace hygiene.
- Facilitates IRC; collects PASS from reviewers.
- Updates `board.md` and `log.md`.
- Decides when the point is 🟢.

## Lifecycle

```
Orchestrator spawns team
        │
        ▼
Reviewer/Spec Reader summarizes scope (optional in Solo)
        │
        ▼
Driver writes smallest change + runs done-signal
        │
        ▼
Reviewer/Spec Reader + Quality Guardian review (if multi-agent)
        │
        ▼
Coordinator/Reviewer marks board.md 🟢 and appends log.md entry
```

## Communication rules

- Technical discussion happens in IRC or file comments.
- The Driver acts on concrete next steps only.
- Disagreements about spec → Spec Reader wins; about quality → Quality Guardian wins; about priority/flow → Coordinator wins.
- Deadlock → Coordinator escalates to user.

## When a point is done

A point flips to 🟢 only when:

1. Driver: done-signal passes.
2. Reviewer/Spec Reader: output matches the point briefing and `design-contract.md`.
3. Quality Guardian: no quality findings (if pod/squad mode).
4. Coordinator/Reviewer: `board.md` updated (and `log.md` if pod/squad mode).
