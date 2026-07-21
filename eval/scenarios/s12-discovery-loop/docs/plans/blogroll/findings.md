# Findings — Blogroll bug sweep (P-01)

Confirmed findings tracker. Hard budget: 5 rounds total. Done: two consecutive rounds surfacing zero new findings.

| ID | Round | Finding | Status |
|---|---|---|---|
| F-01 | 1 | `host()` returned `''` for protocol-relative URLs | fixed — regex accepts the `//` prefix |
| F-02 | 1 | `canonical()` did not lowercase; duplicate cache keys | fixed with `.lower()` |

Rounds used: 3 of 5. Rounds 2 and 3 each surfaced zero new confirmed findings ⇒ K=2 consecutive dry rounds ⇒ converged. No new findings; two by-design patterns remain rejected (not tracked).
