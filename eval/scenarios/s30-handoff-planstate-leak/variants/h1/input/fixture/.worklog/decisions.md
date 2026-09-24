# Decisions — recondata initiative

Locked in; bring new information before reopening any of these.

## Primary match key
Match primarily on account number, falling back to normalized name only when the account number
differs. (2026-05-04)

## Name-only matches
A name-only match (no account-number overlap at all) is always routed to "needs a human" — never
auto-merged. (2026-05-08)

## Tie-breaking
When two old records both plausibly match one new record, the tie goes to whichever old record comes
first in the file. (2026-05-08)
