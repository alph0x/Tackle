# Step 8 — Resume

Re-enter an existing plan. Read in order:
1. `AGENTS.md`
2. Last `log.md` entry
3. `decisions.md`
4. `questions.md`
5. Relevant `points/P-0N.md`
6. Depth artifacts if they exist

Open with a digest and re-ask user-owned open `Q-xx` directly in chat. Report grounding age from the newest ground `Last-verified:` in `log.md` — older than the window (default 14 days, workspace-overridable in `AGENTS.md`) ⇒ recommend re-ground before execution.
