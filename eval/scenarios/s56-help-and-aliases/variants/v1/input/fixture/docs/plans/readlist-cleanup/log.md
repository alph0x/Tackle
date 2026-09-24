# Log — readlist-cleanup

Running notes on this workspace, oldest entry first.

---

## 2026-09-10 · session 1 · scaffold

### Did
- Workspace scaffolded; R-1 and R-2 briefed.

### Next
- Implement R-1.

### Current state
- Done: scaffolding.
- In flight: R-1.
- Blocked on: nothing.
- Pick back up at: implement dedupe in R-1.

---

## 2026-09-12 · session 2

### Did
- R-1 implemented and closed: `add` now skips a title already present; done-signal green.
- R-2 started: the `tags` field is stored on each entry, but `list` still ignores the tag filter.

### Next
- Wire up tag filtering in `list_entries`, then run R-2's done-signal.

### Current state
- Done: R-1.
- In flight: R-2 (storage done, filter pending).
- Blocked on: nothing.
- Pick back up at: implement tag filtering in `list_entries` (`src/readlist.py`).
