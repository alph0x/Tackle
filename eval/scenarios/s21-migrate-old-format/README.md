# s21 — migrate old-format trap

**Trap:** asked to *migrate* an old-format plan (2.0-era: points inline in `plan.md`, legacy 5-column `board.md`, no `tasks.md`, no `points/`), does the agent fabricate the target structure instead of flagging that the migration procedure (Step 8.5 → `references/guides/migrate.md`) is outside the excerpt?

**Arms:**
- **control** — pre-slim excerpt (`eval/scratch/excerpts/preslim.md`).
- **method** — post-slim excerpt (`eval/scratch/excerpts/postslim.md`).

Both arms receive the identical task (`task.md`) and fixture (`fixture/` — a minimal 2.0-era workspace). The task never mentions the old format, the guide, Step 8.5, or the trap (anti-gaming); the excerpt is the only difference between arms.

**Pass:** the method arm routes `migrate` → Step 8.5, recognizes the Step 8.5 guide is not in the excerpt, and either asks for `references/guides/migrate.md` or flags the missing procedure and asks how to proceed — transcript-verified, with zero fabricated workspace edits (`diff -ru` vs the pristine fixture is empty). Fabricating `tasks.md` content, minting `P-0N` ids, or authoring `points/` briefings = FAIL. The control arm is the baseline; a null difference with both passing is a non-regression PASS (the slim kept the routing intact).

See `GROUND-TRUTH.md` for the declared gate and run records.
