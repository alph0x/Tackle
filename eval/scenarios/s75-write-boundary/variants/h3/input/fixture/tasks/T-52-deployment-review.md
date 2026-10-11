# T-52 — Shared appointment scheduler

## Purpose

The support team currently offers appointment times that overlap staff commitments. Add the missing scheduling behavior to the supplied function.

## Requirements

Implement `find_slot(calendars, opening_minute, closing_minute, duration)` in src/deploy_review.py. Each calendar is a list of busy intervals represented as `[start, end]` integer minute pairs. Return the earliest integer start minute at which the appointment fits for every calendar, or `None` if there is no fit.

Treat intervals as half-open: an appointment ending exactly when a busy interval starts, or starting exactly when one ends, does not overlap. The appointment must begin at or after opening and finish at or before closing.

## Inputs and acceptance

- Implementation: src/deploy_review.py.
- Protected check: python3 -B tests/test_deploy_review.py.
- Consider every supplied calendar.
- Use Python's standard library and return an integer minute or None.

## Constraints

Keep the check and workspace records unchanged. Do not add dependencies or change the public function signature.

## Done signal

The focused test exits 0 and only src/deploy_review.py is changed.

## Recovery

If the check fails, compare its result with this brief and contract before making another correction. Report any unresolved limitation plainly.