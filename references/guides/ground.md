# Step 7.5 — Ground (mechanical citation read)

Triggered by `/tackle-ground`. Run this before `/tackle-verify` or `/tackle-implement` to remove the mental load of remembering which `file:line` citations have been read.

**Principle: outsource the memory.** The agent should not rely on its session transcript to know what is grounded. This command produces an explicit, inspectable record.

## Process

1. **Collect citations** — scan `plan.md` §5 and every `points/P-*.md` Context for `path/to/file:NN` references.
2. **Drift-check each one** — for every anchored citation `path:NN — "fragment"`, run the two-phase check. Zero model judgment — the check decides.
   - **Phase 1 — line check**: `sed -n 'NNp' path | grep -Fq "fragment"` → exit 0 = **grounded**. Nothing else runs.
   - **Phase 2 — whole-file fallback** (only on phase-1 failure): count the lines in `path` containing the fragment. Exactly 1, at line MM ⇒ **drifted → re-anchor**: rewrite the citation `path:NN` → `path:MM` in place (literal string replacement, never regex), zero model judgment; the citation is then grounded. 0 ⇒ **stale** ⇒ the point is **ungrounded**. More than 1 ⇒ **ambiguous** ⇒ flagged with the match count; the point is ungrounded until a more specific fragment is chosen.
3. **Record the result** in `log.md`:
   - List every citation read.
   - Flag any citation that could not be resolved (file missing, line out of range, malformed).
4. **Leave `board.md` untouched** — board statuses stay 🔴🟡⏸🟢 (lint row 3). Grounding is recorded only in the `log.md` entry below and derived from it — never copied into the board or the point file.

## Output

Append to `log.md`:

```markdown
## /tackle-ground — {{datetime}}
Last-verified: {{YYYY-MM-DDTHH:MM:SSZ}}

- P-01: grounded (`src/foo.ts:42 — "return cachedValue"` ✓ · `src/bar.ts:10→23 — "export const retries"` re-anchored ✓)
- P-02: ungrounded (`src/missing.ts:5 — "init()"` stale)
```

Legacy date-only stamps read as start-of-day — conservative; the next ground entry upgrades them.

Any **ungrounded** point blocks `/tackle-implement` and `/tackle-next` until the citation is fixed or explicitly waived by the user.

**Staleness is derived, never copied**: a point's grounding age is the `Last-verified:` date of the newest ground entry that lists it (grep `log.md`) — one source of truth; the stamp never lands in the point file.

## When to run

- Right after `/tackle-plan` finishes.
- Before `/tackle-verify` (verification assumes grounding is already recorded).
- On `resume` / `status` / `next` if the session is cold and the ground log is stale.
- On any cold session when `tackle-check probe <workspace>` reports stale.
