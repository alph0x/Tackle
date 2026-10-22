# Decisions

Closed decisions — **don't revisit without cause**. Single source of truth for *what* was
decided and *why*. **Append-only by superseding**: to change a decision, add a NEW entry
that supersedes the old one (mark the old one superseded); never edit history. The session
`history.md` records *when* each decision was made and links its `D-id`. Open items that still
need deciding live in `questions.md` (a resolved `Q-xx` becomes a `D-xx` here).

**Legend**: ✅ active · ⤴ superseded by D-xx

---

## D-01 · {{title}} · ✅ active · {{YYYY-MM-DD, session N}}

**Decision**: {{what was decided, concretely.}}
**Why**: {{rationale; the tradeoff accepted.}}
**Supersedes**: {{none / D-xx}} · **From**: {{Q-xx if it resolved a question, else "—"}}
**Owner**: {{T-NN whose brief applies this decision}} · **Clauses**: {{design-contract clause ids whose meaning it changes; omit either part, or the line, when none}}
<!-- When overturned: mark this "⤴ superseded by D-yy" and add D-yy below. Don't delete this. -->
