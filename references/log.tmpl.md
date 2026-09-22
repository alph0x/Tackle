# History — {{TITLE}}

**Append-only** history, ascending chronological order (newest at the bottom). One entry per
session: `## YYYY-MM-DD · session N · <title>` with **Did / Decisions / Blockers / Next** and,
at the end of the **newest** entry, a **State snapshot** sufficient to resume without
re-reading history. Keep entries terse (append-only ≠ verbose). Never rewrite old entries. Aim for ≤ 25 lines per session entry, preserving material constraints and record references, leading with the compact block — tasks touched, decisions by D-id, status deltas, verification commands + pass/fail. Reasoning and narrative route to `decisions.md` / `reference-docs/`; the log indexes them, it never re-narrates.
Never log secrets. **The task board `board.md` is canonical current state; this file preserves original history.**

**Archive policy** — the legacy ~400-line warning is workspace-overridable in `AGENTS.md`
(`Log archive threshold: N`, lint row 13). An explicit archive request or a recorded policy within
authorized RUN may move entries older than the last five sessions **verbatim** to `log-archive.md`,
or indexed immutable segments when growth warrants them. STATUS never archives. Preserve original
order, headings, event references, failed attempts and budgets; never edit moved entries. Retain
the newest State snapshot and record before/after sizes once. Follow
[recoverable maintenance](guides/context-lifecycle.md#maintenance-and-interruption); archival is
not permission to retire verification data. Measure read, rewrite, and retained bytes separately.

**Verification entries** — every "acceptance check passed/failed" claim carries:

This block is a summary/index, never raw capture. Link the exact captured command and complete
stdout/stderr/process result; do not reconstruct them from prose. Reuse one observation for all
covered checks. Timestamps and model/effort come from actual observations or are `n/a`. Coordinated work uses this template. Focused work uses its self-contained plan/log/usage
procedure; Direct work keeps a check summary without instantiating this template.

````
**Verification record** — `the literal command`
```
trimmed stdout/stderr (≤ 10 lines, keep counts and exit line)
```
cwd: `{{absolute cwd}}` · runtime: `{{tool/runtime or n/a}}`
start: `{{UTC timestamp or n/a}}` · end: `{{UTC timestamp or n/a}}`
exit: 0 · timeout: false · signal: n/a
revisions: input/code/config/dependency/contract `{{fingerprints or n/a}}`
raw: `{{immutable raw check record path}}`
````

No verification block ⇒ the claim is an assertion, and the task may not become Complete. Keep one immutable raw check
record per validation; unknown telemetry stays `n/a`. See `references/guides/run.md` for
correction counters, interrupted runs, integration evidence, and deliverable acceptance.

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
<!-- Failed attempts: one journal line per attempt, each with its verification block:
attempt N: <what was tried> — failed because <lesson>
On budget exhaustion or no-progress (two consecutive attempts with identical evidence
output), the task becomes ⏸ and the entry carries the escalation packet:
### Escalation — P-NN
- Attempts: N (budget M) · reason: budget | no-progress
- Attempt journal: the per-attempt lines above (with verification blocks, last attempt at minimum)
- Hypothesis: the current best explanation of the failure
- Unblocking question: the smallest question that would unblock → Q-xx (user-owned if applicable)
-->


### Next
- {{...}}

<a id="state-snapshot-keep-current-in-the-newest-entry-only"></a>
### State snapshot (record current state when appending; never edit an older snapshot)
- Task state: {{Ready / In progress / Checking / Complete, with supporting references}}
- In flight: {{active task P-0x, where it stands}}
- Blocked on: {{Q-0x / external}}
- Resume from: {{the one concrete next action}}

- Checkpoint: {{authoritative state revision; last fully recorded event and hash; source membership}}
- Active obligations: {{applicable old decisions, blockers, failure lineage and spent cycles}}

Append a uniquely labelled continuation when a session resumes; do not duplicate session headings.
Write changed events once, with stable references. Do not append the full plan, task board, repeated
reasoning or duplicate command transcripts. Current-work projections are rebuilt separately.
