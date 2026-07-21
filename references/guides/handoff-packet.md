# Handoff packet — portable HANDOFF.md (/tackle-handoff)

Triggered by `/tackle-handoff [initiative]` or a natural phrase like "prepare a handoff". Distinct from the end-of-planning chat digest (the output contract in `SKILL.md`): that one formats a chat digest; this one generates a durable file for a session or person that has nothing else.

Output file: `docs/plans/<initiative>/HANDOFF.md` — a portable single file. **Generated, never hand-maintained; regenerating overwrites it.** Overwriting is sanctioned precisely because the file carries no canonical state — `board.md` and `log.md` do; the packet is a read-only projection of them.

**Cold-session rule**: before generating, read `board.md`, `log.md`, `decisions.md`, and `questions.md` — same rule as every cold-session mode.

## The six sections (always all six, in this order)

1. **Context line** — one line: what the initiative is and why it exists.
2. **State snapshot** — lifted from the newest `log.md` entry (Did / Decisions / Blockers / Next), plus board counts per status. Never re-derive state.
3. **Decisions digest** — active `D-xx`, one line each.
4. **Open questions** — each `Q-xx` with its owner.
5. **Next 3 actions** — the next ready points with their starting prompts.
6. **Reading order** — the workspace files, in the order a cold receiver should read them.

The packet also carries one **weakest-link line** — the initiative's weakest-link point: point id + grade + one-line reason (effective confidence = min over the dependency chain, a documented hand computation over `board.md` + the `plan.md` §5 graph).

A section with nothing to report stays in the packet with "none" — receivers can trust the shape.
