# Step 7.5 — Ground (mechanical citation read)

Triggered by `/tackle-ground`. Run this before `/tackle-verify` or `/tackle-implement` to remove the mental load of remembering which `file:line` citations have been read.

**Principle: outsource the memory.** The agent should not rely on its session transcript to know what is grounded. This command produces an explicit, inspectable record.

## Process

1. **Collect citations** — scan `plan.md` §5 and every `points/P-*.md` Context for `path/to/file:NN` references.
2. **Mechanically read each one** — use `read` (or the harness's equivalent) on every cited file and line range.
3. **Record the result** in `log.md`:
   - List every citation read.
   - Flag any citation that could not be resolved (file missing, line out of range, malformed).
4. **Update `board.md`** — mark every point whose citations are all readable as **grounded**. Unreadable or missing citations mark the point **ungrounded**.

## Output

Append to `log.md`:

```markdown
## /tackle-ground — {{datetime}}

- P-01: grounded (`src/foo.ts:42`, `src/bar.ts:10` read)
- P-02: ungrounded (`src/missing.ts:5` not found)
```

Any **ungrounded** point blocks `/tackle-implement` and `/tackle-next` until the citation is fixed or explicitly waived by the user.

## When to run

- Right after `/tackle-plan` finishes.
- Before `/tackle-verify` (verification assumes grounding is already recorded).
- On `resume` / `status` / `next` if the session is cold and the ground log is stale.
