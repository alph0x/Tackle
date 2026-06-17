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

### Specialist roles (Squad only)

Add specialists when the point's risk justifies it; default Squad = Driver + Reviewer + Quality Guardian + Coordinator + one or more of:

| Specialist | When to add | Responsibility |
|---|---|---|
| **Simplicity Auditor** | Adds code, deps, or abstractions. | Runs the simplicity ladder; cuts speculative flexibility. |
| **Architecture Reviewer** | Changes core structure or new abstractions. | Validates against `foundations.md`, SOLID, long-term shape. |
| **Security Reviewer** | Touches auth, input validation, secrets, or trust boundaries. | Runs the security checklist. |
| **Performance & Concurrency Auditor** | Touches hot paths, parallelism, async/await, locks, or large-N structures. | Measures Big-O and wall-clock impact; checks races, lock ordering, async safety. |
| **Regression Auditor** | Touches `SKILL.md`, routing, or existing templates. | Verifies old triggers and templates still work. |

## Single source of truth for state

- **`board.md`** is the only place that records point status (🔴 🟡 ⏸ 🟢).
- **`log.md`** is append-only history. It records what happened, not the current state.
- **`todo.md`** is for planning-readiness; it is not updated during execution.
- **No IRC status payloads.** Coordination messages are plain prose; the board is where status lives.

## Roles (when used)

### Driver
- Owns code changes, writes files, runs tests, makes the done-signal pass.
- Reports result and changed files.

### Reviewer (Pair mode)
- Verifies output matches the point briefing and `design-contract.md`.
- Reviews for Clean Code, SOLID, conventions, naming.
- Reports PASS or findings.

### Spec Reader (Pod/Squad mode)
- Summarizes must-produce / must-not-touch before the Driver writes.
- Verifies output after the Driver reports done.

### Quality Guardian (Pod/Squad mode)
- Reviews diff for smells, redundancy, SOLID, naming, self-documenting code.

### Coordinator (Pod/Squad mode)
- Owns flow and workspace hygiene; updates `board.md` and `log.md`.
- Collects PASS from reviewers; decides when the point is 🟢.

## Lifecycle

1. Reviewer/Spec Reader summarizes scope (skip in Solo).
2. Driver writes smallest change + runs done-signal.
3. Reviewer/Spec Reader + Quality Guardian review (if multi-agent).
4. Specialist auditors review (if Squad).
5. Coordinator/Reviewer marks `board.md` 🟢 and appends `log.md` entry.

## Communication rules

- Technical discussion in IRC or file comments.
- Driver acts on concrete next steps only.
- Disagreements: spec → Spec Reader; quality → Quality Guardian; simplicity → Simplicity Auditor; performance → Performance & Concurrency Auditor; priority/flow → Coordinator.
- Deadlock → Coordinator escalates to user.

## When a point is done

A point flips to 🟢 only when:

1. Driver: done-signal passes.
2. Reviewer/Spec Reader: output matches briefing and `design-contract.md`.
3. Quality Guardian: no quality findings (if Pod/Squad).
4. Simplicity/Regression/Performance & Concurrency Auditor: no findings (if Squad and triggered).
5. Coordinator/Reviewer: `board.md` updated (and `log.md` if Pod/Squad).
