# Decisions

**Legend**: ✅ active · ⤴ superseded

---

## D-03 · Blank windows are flagged, not guessed · ✅ active · 2026-08-26, session 2

**Decision**: a stop whose window cell is blank gets `no window`.
**Why**: business customers with a blank window take deliveries all day; a guess would mark them late.

## D-04 · Both ends of a window count · ✅ active · 2026-09-02, session 4

**Decision**: a stop that arrives at the opening or at the closing minute of its window is on time.
**Why**: the depot's service agreement says "between 09:00 and 11:00 inclusive"; the dispatcher marks
11:00 arrivals as fine.
