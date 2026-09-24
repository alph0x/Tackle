# recondata — session notes

One entry per work session, oldest first. The latest entry closes with a quick recap of exactly where
things stand.

---

## 2026-05-04 — kickoff

**What happened:** Looked at both exports side by side; found three ways records can look like
duplicates without matching exactly: case differences in the name, a trailing branch-code suffix on the
account number, and a handful of accounts that appear in both files under two entirely different account
numbers.

**Calls made:** Match primarily on account number, falling back to normalized name only when the account
number differs.

**Up next:** Write the normalization step.

---

## 2026-05-08 — normalization done, matching underway

**What happened:** Normalization step done (case-folds names, strips branch-code suffixes from account
numbers); `python3 -m py_compile reconcile.py` is green. Matching pass: exact and normalized-account
matches both work. The "two different account numbers, same person" case is still unhandled.

**Calls made:** A name-only match (no account-number overlap at all) is routed to "needs a human" —
never auto-merged. Ties (two old records both plausibly matching one new record) go to whichever old
record comes first in the file.

**Still open:** How many old records has this actually caught so far — is a spot-check against last
quarter's totals needed before trusting the output? And should low-confidence matches (below whatever
threshold we pick) be auto-flagged for review, or kept silently? Both owned by Dana.

**Up next:** Handle the "two account numbers, same person" case, then write the end-of-run summary
report.

**Where this leaves things:**
- Finished: normalization.
- Underway: matching — exact/normalized-account done, cross-account unhandled.
- Nothing blocking.
- Pick up at: the cross-account matching logic in `reconcile.py`.
