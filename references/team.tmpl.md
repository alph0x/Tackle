# Team protocol — {{TITLE}}

When a point enters execution, the orchestrator spawns a **point team** sized to the point's complexity and risk. In execution this protocol is **mandatory** — every point gets its team, and the checker role (see §When a point is done) is filled by an agent independent from the Driver, using whatever subagent or parallel facility the harness provides. The workspace (`board.md`, `log.md`, the point file, and the touched files) is the single source of truth; the agent messaging channel is only for coordination.

## Model binding

Teams bind roles to **model tiers**, never to vendor models. Three tiers, abstract and harness-agnostic:

- **`fast`** — mechanical work: grounding reads, greps, lint rows, drift checks.
- **`standard`** — implementation, coordination, review.
- **`frontier`** — adversarial verification, red-team, architecture judgment.

Role→tier defaults (a point briefing may override):

| Role | Tier |
|---|---|
| Driver | standard |
| Reviewer / Quality Guardian / Coordinator | standard |
| Spec Reader | fast |
| Verifier / Red-Teamer | frontier |
| Checker (maker/checker) | frontier attempted — see below |
| Specialists (Squad) | standard |

Grounding reads, lint, drill mechanics: `fast`.

Agents are spawned **per role at point execution**, each on its role's bound tier — there are no predetermined agents. The workspace `AGENTS.md` §Model map binds tiers to the concrete models the harness offers; core templates never name vendor models.

**Checker ≠ maker (best-effort, never blocks):** the checker SHOULD run on a different tier than the maker. If the harness cannot bind or isolate tiers, the checker runs on whatever is available and its evidence line in `log.md` records `model-binding: unavailable`. Compliance is recorded, never enforced.

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

- **`board.md`** is the only place that records point status (🔴 🟡 ⏸ 🟢 · ⚪ skipped (optional slice not executed, with one-line reason)). `plan.md` §5 never carries status columns.
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
- **Continuity:** ONE logical Coordinator owns the whole execution. It is long-lived across points and waves where the harness supports persistent agents; where it does not (or across sessions), it re-spawns per point and MUST read `coordinator.md` + `board.md` + `log.md` before its first action. It refreshes `coordinator.md` at every point close — a projection, never canonical; canonical state stays in `board.md`/`log.md`.
- Collects PASS from reviewers; flips 🟢 only after sign-off — Full gate: the Coordinator sign-off section in `reports/P-0N-report.md`; Lite gate: the evidence block recorded in `log.md`.
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
5. Coordinator/Reviewer marks `board.md` 🟢 and appends the `log.md` entry — Full gate only after the Coordinator sign-off section in `reports/P-0N-report.md`; Lite gate after the evidence block in `log.md`.

## When a point is done

Point closure is one protocol: the report file is the communication channel, the named handshake runs through its sections, and the Coordinator sign-off gates the flip.

### Closure report — `reports/P-0N-report.md` (Full gate only)

Every Full-gate point closes with one report file in the workspace `reports/` directory. **Lite-gate points keep their evidence in `log.md` as today (D-11).** `log.md` stays canonical: it keeps a one-line summary + pointer to the report, never the full evidence. Sections, in order, each appended by its owner:

1. **Scope** — Reviewer/Spec Reader: must-produce / must-not-touch summary (skipped in Solo).
2. **INTENT + Evidence** — Driver: INTENT gate lines, attempt journal, done-signal run with its **Evidence** block (command, trimmed output, exit line).
3. **Reviews** — Reviewer/Spec Reader, Quality Guardian, specialists: PASS or findings.
4. **Checker re-run** — independent checker (maker/checker, condition 1 below): done-signal re-run evidence, its **tier** per §Model binding, the reward-hacking guard result, and a `model-binding: unavailable` note when checker ≠ maker could not be honored. When the briefing declares `Lenses:`, it also records the lens list, each lens's verdict, and the vote count.
   It also records the point's **evidence grade**, derived mechanically from the evidence block (never self-declared):
   - **E1 command-verified** ⇔ this section (Lite gate: the `log.md` evidence block) carries command + output + exit line from the independent checker.
   - **E2 review-gated** ⇔ a review-gate marker with rubric + named reviewer (no honest command exists).
   - **E0 UNVERIFIABLE** ⇔ an explicit UNVERIFIABLE label.
   - **E3 asserted** ⇔ anything else.
   Grades are DERIVED, never self-declared; any later re-derivation that disagrees is a grade-inflation finding.
5. **Coordinator sign-off** — verdict (`closed` / `rework` + reason) + regression sweep result. **Solo assisted (L2) points: the human checker writes this section (D-09).** The 🟢 flip requires this section: no sign-off, no flip.

Solo points compress to sections 2 + 4 + 5.

### Closure handshake

1. Driver → `closure-request` (point id + report pointer) after writing its INTENT + Evidence section.
2. Checker → `closure-verdict` (re-run result + reward-hacking guard result) via the Checker re-run section.
3. Coordinator → `sign-off` (flip authorized) or `rework` (finding + owner) via the Coordinator sign-off section.

The report file is the record — each agent appends its section. Where the workspace harness map records `agent-messaging: supported`, the same messages MAY also travel over the agent messaging channel for rework speed; the file remains the record either way.

**Rework bound (D-10):** at most **2 closure-rework cycles** per point, separate from the Driver's budget of 3 failed fix-verify cycles. Exhaustion ⇒ the point is marked blocked (⏸) and the Coordinator files the escalation packet.

### Communication rules

- Technical discussion in the agent messaging channel or file comments.
- Driver acts on concrete next steps only.
- Disagreements: spec → Spec Reader; quality → Quality Guardian; simplicity → Simplicity Auditor; performance → Performance & Concurrency Auditor; priority/flow → Coordinator.
- Deadlock → Coordinator escalates to user.

### Opt-in `Lenses:` field (multi-lens checker)

A point briefing MAY declare **`Lenses:`** — a list of distinct verification lenses (e.g. `correctness, security, repro`). Absent ⇒ today's single checker, unchanged. When declared, done-condition 1 runs as N independent skeptic checks decided by majority vote (see below), and closure report section 4 records the lens evidence.

### Done-conditions

A point flips to 🟢 only when every condition holds; each maps to a report section (Lite gate: same conditions, evidence in `log.md`):

1. **maker/checker**: the Driver's own done-signal run is informative, never gating. The 🟢-flipping run and its evidence come from an **independent checker** — tiered by autonomy: Pair/Pod/Squad: the Verifier or Coordinator; Solo assisted (L2): the human confirms after seeing the evidence; Solo unattended (L3) or any production-path point: an independent fresh session/subagent reading only the point file and workspace state. If the harness cannot isolate a fresh session, fall back to the human checker and record that fallback in `log.md`. (Report section 4 names the checker's tier.) When the briefing declares `Lenses:`, the checker runs N independent skeptic checks, one per lens — N ≥ 2, lenses distinct in kind, not rewordings — and a finding survives only under majority vote (⌈N/2⌉ lenses pass it); skeptic lenses inherit the checker's tier binding (frontier attempted, `model-binding: unavailable` recorded when unbindable), and the reward-hacking guard (condition 2) still reopens on loosened checks regardless of the vote.
2. **Reward-hacking guard**: the checker greps the diff for removed, disabled, or loosened tests, assertions, or done-signals unless the point's Goal explicitly requires it. Any such change reopens the point (🟢 → 🟡) and blocks the current one. (Report section 4 records the result.)
3. **Verifier / Red-Teamer**: `/tackle-verify` passed with no HIGH findings and no unresolved MEDIUM findings.
4. Driver: done-signal passes **with its Evidence block recorded** — in the report (Full) or in `log.md` (Lite).
5. Reviewer/Spec Reader: output matches briefing and `design-contract.md`.
6. Quality Guardian: no quality findings (if Pod/Squad).
7. Simplicity/Regression/Performance & Concurrency Auditor: no findings (if Squad and triggered).
8. Coordinator: `board.md` flipped 🟢 and `log.md` appended — one-line summary + pointer (Full) or the evidence entry (Lite).
9. **Regression sweep**: done-signals of every 🟢 point with intersecting Touches re-ran green; any failure reopens that point (🟢 → 🟡) and blocks this one. (Report section 5 records the result.)
