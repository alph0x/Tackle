# Board — checkout-redesign

**Canonical status board.** `board.md` is the only file that records point status.

Status: 🔴 not started · 🟡 in progress · ⏸ blocked · 🟢 done · ⚪ skipped (optional slice not executed, with one-line reason).
Confidence: E1 command-verified · E2 review-gated · E3 asserted · E0 UNVERIFIABLE.

| Point | What | Depends on | Status | Confidence |
|---|---|---|---|---|
| P-01 | Replace the 3-step checkout with a single-page flow | — | 🟢 | E2 |
| P-02 | Port the payment splitter to the new flow | P-01 | 🟢 | E2 |
| P-03 | Add the inline order-summary block | P-01 | 🟢 | E2 |
| P-04 | Deprecate the legacy checkout route | P-02, P-03 | 🟢 | E2 |

### Dependency graph

```
P-01 → P-02 → P-04
P-01 → P-03 → P-04
```
