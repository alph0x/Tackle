# Pending skill fixes (intake list for future planning)

**Purpose:** retro lessons that are skill fixes, collected so they don't die in retro.md files. **Intake rule:** `/tackle-plan` Step 1 reads this file when it exists and offers applicable items as points or chores. Remove items as they ship; add items from any retro.

## Open

- (none)

## Shipped

- **Attempt-budget metric recipe** — recipe broadened to `grep -i "budget\|attempts" AGENTS.md` (rule 5 of AGENTS.tmpl.md already declares the 3-attempt loop budget; compact hand-written workspace AGENTS.md files should carry the same line). Shipped in 3.4.0 (retro.tmpl.md).
- **Comprehension-debt recipe** — split into real debt (no checker evidence in log) vs accepted debt (checker-verified, human-unread, informational). Shipped in 3.4.0 (retro.tmpl.md).
- **Lint-safe notation** — one line in lint-spec.md: discuss scanned symbols (status glyphs, placeholder braces) via U+XXXX prose notation and `$'\uXXXX'` shell escapes so rows 1/5 don't self-flag. Shipped in 3.4.0.

## Notes

- D-10 rework-budget calibration (model-teams): still no rework observed across two initiatives — keep the number; revisit when a rework actually happens.
