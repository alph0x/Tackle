# Step 9 — Status / List / Next

- **Status**: read-only digest from `board.md` + last log snapshot; report grounding age from the newest ground `Last-verified:` in `log.md` — older than the window (default 14 days, workspace-overridable in `AGENTS.md`) ⇒ recommend re-ground before execution.
- **List**: scan `docs/plans/*/`; one line each.
- **Next**: print the next ready point's pre-attack summary + ready-to-paste prompt.
