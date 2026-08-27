# Step 9 — Status / List / Next / Resume / Handoff

One command family: `/tackle-status` (digest/list/resume/handoff), read-only except the optional `--handoff` write.

- **Status** — read-only digest from `board.md` + last log snapshot; report grounding age and the re-ground recommendation.
- **List** — scan `docs/plans/*/`; one line each.
- **Next** — print the next ready point's pre-attack summary + ready-to-paste prompt. Read-only: it selects and prepares, it never executes.
- **Resume** — re-enter an existing plan (cold-session read-first).
- `--handoff` — generate a portable `HANDOFF.md`.

## Resume — cold-session read-first

Read in order: `AGENTS.md` → last `log.md` entry → `decisions.md` → `questions.md` → relevant `points/P-0N.md` → depth artifacts if they exist.

Open with a digest and re-ask user-owned open `Q-xx` directly in chat. Report grounding age from the newest ground `Last-verified:` in `log.md` — older than the window (default 14 days, workspace-overridable in `AGENTS.md`) ⇒ recommend re-ground before execution. The log stamp never substitutes for a this-session read: run `tackle probe <workspace>` — it compares every cited file's mtime against the newest `Last-verified:` stamp and lists stale files; any stale ⇒ re-ground before the point can be ready.

## /tackle-status — standing-loop digest (ex-pulse)

Triggered by `/tackle-status <ws>` or "status" — typically by a scheduler: cron, a CI job, a platform automation, anything that can start an agent session. The scheduler is the harness's business; Tackle defines only the contract of the invocation.

**Non-mutating.** A status digest reads `board.md`, `decisions.md`, the newest `log.md` entry (heading `## YYYY-MM-DD` to end of file), and `questions.md` if any question is open — never the full `log.md`; full-history reads belong to retro mining, which reads the archive pair. It may run the documented check commands — citation-drift checks, the lint table, the regression sweep — none of which modify the tree. The only write allowed is an optional `log.md` entry marked `status`. It never edits source or board and never executes points; execution still requires explicit intent. A Methodology stamp older than the current release is reported with a migrate offer (`status.md` → `migrate.md`).

**One digest, ≤ 12 lines**, one line per item:

1. Stale citations (`tackle probe` result, plus grounding age vs the workspace window).
2. The `lint: N/M checks passed` score line.
3. Regression-sweep result.
4. Cross-initiative collisions.
5. Blocked points with their escalation packets.
6. The next ready point with its ready-to-paste starting prompt.
7. The weakest-link line — the initiative's weakest-link point: point id + grade + one-line reason (effective confidence = min over the dependency chain, a documented hand computation over `board.md` + the `plan.md` §5 graph).
8. Usage so far (optional) — tokens by phase from `usage.md` when the workspace carries one (report the `n/a`-row count too); omit the line when there is no `usage.md`.
9. `log.md` size vs its archive threshold (lint row 13); over ⇒ recommend the archive protocol — a status digest never archives.

The point of the digest: a human skimming notifications stays the engineer in the loop. On a busy workspace, counts + pointers, never listings.

## Archive (on consent)

Status digests are read-only — they never archive. On an explicit user ask, run the `log.tmpl.md` archive protocol: move entries older than the last 5 sessions **verbatim** from `log.md` to `log-archive.md` (append, ascending), never edit moved entries, and confirm the newest entry still carries its State snapshot. Threshold: `Log archive threshold: N` in the workspace `AGENTS.md`, default 400 lines. Close with a one-line `log.md` entry recording the archive (entries moved, line counts before/after). Lint row 6 covers the archive pair's ordering.

## Handoff — portable HANDOFF.md (/tackle-status --handoff)

Triggered by `/tackle-status <ws> --handoff` or a natural phrase like "prepare a handoff". Generates a durable file for a session or person that has nothing else.

Output file: `docs/plans/<initiative>/HANDOFF.md` — a portable single file. **Generated, never hand-maintained; regenerating overwrites it.** Overwriting is sanctioned precisely because the file carries no canonical state — `board.md` and `log.md` do; the packet is a read-only projection of them.

**Cold-session rule**: before generating, read `board.md`, `log.md`, `decisions.md`, and `questions.md` — same rule as every cold-session mode.

### The six sections (always all six, in this order)

1. **Context line** — one line: what the initiative is and why it exists.
2. **State snapshot** — lifted from the newest `log.md` entry (Did / Decisions / Blockers / Next), plus board counts per status. Never re-derive state.
3. **Decisions digest** — active `D-xx`, one line each.
4. **Open questions** — each `Q-xx` with its owner.
5. **Next 3 actions** — the next ready points with their starting prompts.
6. **Reading order** — the workspace files, in the order a cold receiver should read them. When the workspace files cannot be summarized without leaking plan-local paths or ids, this section states **`none — self-contained`**.

**Portability rule** (binds every section): the packet is **portable** — it carries its context **inline**, never as references to **gitignored** plan-local state. No `docs/plans/` paths (not even the packet's own), no "see `<workspace file>`" pointers, no bare D-xx / Q-xx / point ids. The receiver "has nothing else", and the plan workspace commonly does not travel (convention 9: `docs/plans/` is gitignored by scaffold default), so any pointer into it breaks on the other machine. Every id appears only with its content inline; every section carries the state itself.

The packet also carries one **weakest-link line** — the initiative's weakest-link point: point id + grade + one-line reason (effective confidence = min over the dependency chain, a documented hand computation over `board.md` + the `plan.md` §5 graph).

A section with nothing to report stays in the packet with "none" — receivers can trust the shape.
