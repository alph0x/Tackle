# Trace — coverage matrix (/tackle-trace)

Triggered by `/tackle-trace [initiative]` or a natural phrase like "trace coverage". Read-only reporting: it never edits `board.md`, points, or source; fixes to what it finds are new points or `Q-xx` entries, decided by the user.

**Principle: count-assert both ways.** Per-point anchoring checks one point at a time; a criterion covered by no point is invisible to them. The matrix closes that direction.

## Inputs

- **Acceptance criteria** from `spec.md`, the ticket, or `constitution.md`. If none exists, trace against `plan.md` §Acceptance criteria and say so in the output; a plan with no criteria at all is itself a **HIGH** finding.
- **Points and anchors** from `plan.md` §5 and each briefing's `Traces to` line in `points/*.md`.

## Output

One row per criterion, exactly this header:

```
| Criterion (spec/ticket anchor) | Points | Status |
```

- Status vocabulary: `covered` / `gap`.
- Count-assert both ways: criteria count == matrix rows, AND every point id in `plan.md` §5 appears in some row or is listed under a closing **Scope drift** list.
- Orphan criterion (no point) ⇒ coverage **gap**; point with no anchor ⇒ **scope drift**. Both are **HIGH** findings, with the same blocking semantics as verify.

## Where results go

- Append the matrix to `log.md` as the session's evidence block.
- Report a digest ≤ 12 lines in chat per the output contract — point to the log entry, don't paste the whole matrix.
