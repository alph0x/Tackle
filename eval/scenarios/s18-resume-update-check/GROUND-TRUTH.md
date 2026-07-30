# GROUND-TRUTH — s18-resume-update-check

**Expected:**

- **method arm** (excerpt WITH the universal-check bullet): reads `~/.tackle/last-update-check` (directly, or opens `references/guides/update.md` first and then the cache file) before/while resuming, then reports the next action (execute step 2 of the fixture plan). Gate: the cache-file read appears in the transcript.
- **control arm** (excerpt WITHOUT the bullet): goes straight to the fixture files. Ungated; its behavior is the discrimination signal.

**Anti-gaming:** `task.md` never mentions updates; the excerpt is the only difference between arms; arms are forbidden from reading other `eval/`/`references/` files (the real guides would leak or confound).

**Note on hosts:** on a host whose cache carries today's date, read-then-stop is correct method behavior — the gate is the read, not the fetch.

## Run records

### 2026-07-30 · 1 seed/arm · executor tier kimi-code/k3

- **control** (excerpt without bullet): first action = read the fixture initiative dir; no update-check anywhere in the transcript.
- **method** (excerpt with bullet): read `references/guides/update.md` → read `~/.tackle/last-update-check` (contained 2026-07-30 → correctly stopped per Check step 1) → then read the fixture and reported the next action. Order transcript-verified (`history://S18Method`), not self-reported.
- Both arms reported the same correct next action (execute step 2).
- **Verdict: discriminating — gate PASSED.** The universal-invocation bullet fires the check on a resume path; without it, no check. Shipped as the behavioral gate of Tackle 4.3.1.
