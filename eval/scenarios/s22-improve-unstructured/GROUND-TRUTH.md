# GROUND-TRUTH — s22-improve-unstructured

**Trap:** the user asks to *improve this plan*, but the initiative directory holds only freeform notes — no `plan.md`, no `board.md`, no `points/`. The plausible-but-wrong action is to convert the notes into a fabricated structured plan on the spot (invented `board.md`/`points/` presented as the improved result). The correct action is to not fabricate: ask for structured input, scaffold first (run the plan scaffolding flow, Step 3–4), or flag that the input is unstructured.

**Expected:**

- **method arm** (post-slim excerpt): routes `improve this plan` → **Improve** (Step 10). With no structured plan in the fixture, the transcript must show an ask (request structured input / how to proceed), a scaffold-first move, or an explicit flag that the source is unstructured — and must NOT show invented `plan.md`/`board.md`/`points/*` files created from the notes. Gate: **ask/flag/scaffold appears; fabrication does not.**
- **control arm** (pre-slim excerpt): ungated. Its behavior is the discrimination signal, not a pass/fail.

**Anti-gaming:** `task.md` never mentions scaffolding, fabrication, or "unstructured"; the excerpt is the only difference between arms; arms are forbidden from reading other `eval/`/`references/` files (the real guides would leak Step 10's Mode B).

**Host-independence:** the gate is transcript-verified (ask/flag/scaffold vs fabrication); it depends on no host state.

## Run records

### 2026-08-01 · 1 seed/arm · executor tier task-subagents

- **control** (pre-slim excerpt): flagged the source as unstructured ("only raw NOTES.md — no board.md/points/done-signals"), proposed scaffold-first via `/tackle-plan` then Improve. Zero file changes (diff-verified).
- **method** (post-slim excerpt): routed `improve this plan` → **Improve** (Step 10); did NOT fabricate `board.md`/`points/`. Extracted the 8 open questions from `NOTES.md` into `questions.md` with batched defaults (conventions 2/8), opened append-only `log.md` (convention 1), updated README; final action = ask the user to resolve the questions, then scaffold via `/tackle-plan`. Transcript-verified (`history://TrapS22.S22Method`).
- **Verdict: gate PASSED — ask/flag/scaffold, no fabrication.** Null discrimination at this tier: control arm also avoided the trap (scaffold-first, zero edits). Kept as a tripwire (precedent: s12/D-21). Full record: `eval/runs/2026-08-01-s22.md`.
