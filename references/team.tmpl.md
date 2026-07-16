# Team protocol — {{TITLE}}

When a point enters execution, the orchestrator spawns a **point team** sized to the point's complexity and risk. In execution this protocol is **mandatory** — every point gets its team, and the checker role (see §When a point is done) is filled by an agent independent from the Driver, using whatever subagent or parallel facility the harness provides. The workspace (`board.md`, `log.md`, the point file, and the touched files) is the single source of truth; the agent messaging channel is only for coordination. The team is harness-agnostic: "the most capable model" handles planning/judgment, "the balanced model" handles validation, "the fast model" handles mechanical work. Use whatever model selection your harness provides.

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

- **`board.md`** is the only place that records point status (🔴 🟡 ⏸ 🟢). `plan.md` §5 never carries status columns.
- **`log.md`** is append-only history. It records what happened, not the current state.
- **`todo.md`** is for planning-readiness; it is not updated during execution.
- **No status payloads over the agent messaging channel.** Coordination messages are plain prose; the board is where status lives.

## Roles (when used)

### Driver
- Owns code changes, writes files, runs tests, makes the done-signal pass.
- Before any behavior-changing edit, writes the INTENT gate line per the point briefing: `INTENT: current code does <X>; done-signal expects <Y>; <source> says <Z>.` If X, Y, and Z do not agree, surfaces the contradiction and stops.
- Self-corrects up to **3 failed fix-verify cycles on the same issue**; after that, stops, reports the actual output and current hypothesis, and escalates.
- Reports result and changed files, with its **Evidence** block (command, trimmed output, exit line).
- Owns the attempt journal: appends one line per failed attempt, re-reads prior lines before retrying.

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
- Collects PASS from reviewers; flips 🟢 only when the evidence block is recorded in `log.md`.
- On budget exhaustion or no-progress, flips the point ⏸ and files the escalation packet.

### Verifier / Red-Teamer
- Runs `/tackle-verify` on the point before it is handed to the Driver.
- Produces a findings list with certainty levels (HIGH/MEDIUM/LOW).
- Uses `references/failure-modes.md` as a checklist to name the risk created by skipped or faked execution steps.
- A HIGH finding blocks execution; MEDIUM blocks unless the user accepts the risk; LOW is advisory.
- Independent from the Driver and Reviewer; can be the same agent as the Coordinator only on trivial Solo points.

## Lifecycle

1. Reviewer/Spec Reader summarizes scope (skip in Solo).
2. Driver writes smallest change + runs done-signal.
3. Reviewer/Spec Reader + Quality Guardian review (if multi-agent).
4. Specialist auditors review (if Squad).
5. Coordinator/Reviewer marks `board.md` 🟢 and appends `log.md` entry.

## Communication rules

- Technical discussion in the agent messaging channel or file comments.
- Driver acts on concrete next steps only.
- Disagreements: spec → Spec Reader; quality → Quality Guardian; simplicity → Simplicity Auditor; performance → Performance & Concurrency Auditor; priority/flow → Coordinator.
- Deadlock → Coordinator escalates to user.

## When a point is done

A point flips to 🟢 only when:

1. **maker/checker**: the Driver's own done-signal run is informative, never gating. The 🟢-flipping run and its evidence come from an **independent checker** — tiered by autonomy: Pair/Pod/Squad: the Verifier or Coordinator; Solo assisted (L2): the human confirms after seeing the evidence; Solo unattended (L3) or any production-path point: an independent fresh session/subagent reading only the point file and workspace state. If the harness cannot isolate a fresh session, fall back to the human checker and record that fallback in `log.md`.
2. **Reward-hacking guard**: the checker greps the diff for removed, disabled, or loosened tests, assertions, or done-signals unless the point's Goal explicitly requires it. Any such change reopens the point (🟢 → 🟡) and blocks the current one.
3. **Verifier / Red-Teamer**: `/tackle-verify` passed with no HIGH findings and no unresolved MEDIUM findings.
4. Driver: done-signal passes **with its evidence block recorded in `log.md`**.
5. Reviewer/Spec Reader: output matches briefing and `design-contract.md`.
6. Quality Guardian: no quality findings (if Pod/Squad).
7. Simplicity/Regression/Performance & Concurrency Auditor: no findings (if Squad and triggered).
8. Coordinator/Reviewer: `board.md` updated (and `log.md` if Pod/Squad).
9. **Regression sweep**: done-signals of every 🟢 point with intersecting Touches re-ran green; any failure reopens that point (🟢 → 🟡) and blocks this one.
