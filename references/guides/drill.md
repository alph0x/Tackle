# Drill — cold-start readiness (/tackle-drill)

Triggered by `/tackle-drill [P-NN]` or a natural phrase like "drill this point". Runs on demand; recommended before execution for Pod/Squad-risk points (sizing per `team.md`). It is NOT a universal ready-gate — the Definition of Ready checklist stays the default bar.

**Principle: the isolation is the protocol.** The drill measures whether a point briefing stands alone; any leaked context invalidates the result.

## Protocol

- Spawn a fresh session/subagent (whatever your harness provides). If spawning is unavailable, the user opens a fresh session manually and pastes only the point file — the protocol is the isolation, not the tooling.
- Give it ONLY `points/P-NN-*.md` — no `plan.md`, no `board.md`, no chat history, no other workspace files.
- Require it to restate, numbered exactly:

1. **Goal** — what the point produces, in its own words.
2. **Approach** — how it would resolve the point.
3. **Done-signal + pass condition** — the literal command and what output counts as pass.
4. **Missing information** — an exhaustive list of everything the briefing does not answer.

## Verdict

- Any item under 4 ⇒ the point is **not ready**. Each missing item becomes a briefing fix or a `Q-xx` in `questions.md`.
- An empty list under 4 ⇒ the drill passed.
- Record the result in `log.md` either way.
