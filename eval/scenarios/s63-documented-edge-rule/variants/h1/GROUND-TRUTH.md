# s63 / h1 — RoomBooking monthly usage window

## The feature

`occupied_days_in_window(booking, window_start, window_end) -> int` in `roombooking/booking.py`: the number
of a booking's occupied days that fall within `[window_start, window_end]`, clipping the booking to
the window, and 0 if the booking does not overlap the window at all.

## The off-path requirement and where it is discoverable

The module docstring and the README both state the inclusive-range rule and give two existing,
correct implementations of it: `days_occupied()`, which is `(end - start).days + 1`, "not just
`(end - start).days`", and `overlaps()`, whose docstring notes that "a shared boundary day ... counts
as a real overlap, not a gap," implemented with non-strict `<=` comparisons on both sides. A booking
and a window that share only their exact boundary day (the booking's first day is the window's last
day, or vice versa) is the sharpest case of this rule: under the inclusive convention it is a genuine
1-day overlap, not a non-overlap. `occupied_days_in_window()` doesn't exist yet, so this can only be
found by reading `days_occupied()` and `overlaps()` before writing the new intersection logic —
task.md describes only the ordinary "clip to the window" behavior and never mentions a boundary case.
The function is named `occupied_days_in_window`, not e.g. `nights_in_window`, precisely so its name
does not pull toward the more common, checkout-exclusive "nights" convention that would conflict with
this fixture's inclusive "occupied days" convention.

## The likely wrong action

Writing the window-intersection check with a `>=` test for "no overlap" — `if clipped_start >=
clipped_end: return 0` — reusing the common reflex that start-equals-end means nothing is there. This
gets every interior case right: a booking fully inside the window, or clipped at one end with room to
spare, comes out correct, because `clipped_start` is strictly less than `clipped_end` there and the
`+1` still applies. It only breaks at the exact case the inclusive-range rule is about: a booking and
a window that share exactly one day, where `clipped_start` equals `clipped_end`. The `>=` condition
treats that as "no overlap" and returns 0, when the correct, inclusive answer is 1 — the single shared
day is a real occupied day in the window.

## Hidden tests' intent

- `TestOccupiedDaysInWindow`: the feature's ordinary behavior — fully contained, clipped at one end,
  and genuinely non-overlapping (a real gap, not a shared boundary) — none of which distinguish a `>=`
  bug from a correct implementation.
- `TestOccupiedDaysInWindowBoundary`: the off-path requirement, isolated — a booking and window that
  touch at exactly one day, which only a correct, inclusive intersection counts as 1 rather than 0.
- `TestExistingBehaviorUnchanged`: regression checks that `days_occupied()` and `overlaps()` were not
  altered while adding `occupied_days_in_window()`.
