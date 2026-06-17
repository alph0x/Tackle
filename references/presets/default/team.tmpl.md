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

| Specialist | When to add | Responsibility |
|---|---|---|
| **Simplicity Auditor** | Any point that adds code, dependencies, or abstractions. | Runs the simplicity ladder: does this need to exist? stdlib? native? installed dep? one line? Cuts speculative flexibility, factories with one product, config for static values, and boilerplate. |
| **Architecture Reviewer** | Point changes core structure or introduces new abstractions. | Validates the change against `foundations.md`, SOLID, and the long-term shape of the codebase. |
| **Security Reviewer** | Point touches auth, input validation, secrets, or trust boundaries. | Runs the security checklist from `design-contract.md` / `SKILL.md` Step 6 and flags vulnerabilities. |
| **Test Engineer** | Point needs non-trivial test coverage or test infrastructure. | Designs tests, verifies edge cases, ensures the done-signal is meaningful. |
| **Integration Reviewer** | Point affects multiple subsystems or external contracts. | Checks cross-file impact and migration path for callers. |
| **Risk Manager** | Point has high blast radius or many unknowns. | Tracks assumptions, flags blockers early, and ensures rollback plan exists. |
| **Regression Auditor** | Any point that touches `SKILL.md`, routing, or existing templates. | Verifies old triggers and templates still work; catches silent breakage of Tackle 1.x behavior. |
| **Boundary Auditor** | Point touches trust boundaries, sensitive data, or scope-delimited files. | Verifies nothing leaks outside `Touches`, no secrets exposed, no permissions widened. |
| **Contract Auditor** | Points where `contract.md` is the authority. | Formal line-by-line check that the implementation matches the contract beyond what Spec Reader covers. |
| **Testability Auditor** | When the done-signal is complex or relies on external tooling. | Verifies the done-signal is mechanical, reproducible, and fails red when the logic breaks. |
| **Doc Auditor** | When the point changes the public surface. | Verifies `README.md`, `SKILL.md`, `CHANGELOG.md`, and methodology stamps reflect the change. |

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
Specialist auditors review (if Squad)
        │
        ▼
Coordinator/Reviewer marks board.md 🟢 and appends log.md entry
```

## Communication rules

- Technical discussion happens in IRC or file comments.
- The Driver acts on concrete next steps only.
- Disagreements about spec → Spec Reader wins; about quality → Quality Guardian wins; about simplicity → Simplicity Auditor wins; about priority/flow → Coordinator wins.
- Deadlock → Coordinator escalates to user.

## When a point is done

A point flips to 🟢 only when:

1. Driver: done-signal passes.
2. Reviewer/Spec Reader: output matches the point briefing and `design-contract.md`.
3. Quality Guardian: no quality findings (if pod/squad mode).
4. Simplicity Auditor: no over-engineering findings (if squad mode).
5. Regression Auditor: no regression findings (if squad mode and point touches existing surface).
6. Doc Auditor: no documentation gaps (if squad mode and point changes public surface).
7. Coordinator/Reviewer: `board.md` updated (and `log.md` if pod/squad mode).
