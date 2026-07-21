# Log — Blogroll link helpers

## 2026-07-18

### Did
- Gate: Lite. Plan written, P-01 briefed and started.
- P-01 round 1: F-01, F-02 confirmed and fixed (see `findings.md`). Two further candidate patterns reviewed and rejected as by-design: protocol-relative URLs passing through `canonical()` unnormalized, and trailing-slash collapse sharing cache keys. Not tracked — won't fix.

### Decisions
- None.

### Blockers / open questions
- None.

## 2026-07-19

### Did
- P-01 round 2: re-sweep; the same two by-design patterns re-noted, still rejected; zero new confirmed findings. `python3 links.py` exits 0.

### Decisions
- None.

## /tackle-ground — 2026-07-19 09:58
Last-verified: 2026-07-19

- P-01: grounded (`links.py:5 — "PROTOCOLS = ("` ✓)

## 2026-07-21

### Did
- P-01 round 3: re-swept `links.py`. Only candidate patterns present are the two already-seen by-design rejections — protocol-relative `//` URLs returning unnormalized from `canonical()` (`links.py:14-15`) and trailing-slash collapse sharing cache keys (`links.py:16`). Both recorded rejected in rounds 1-2; deduped against everything seen, not re-filed. Zero new confirmed findings. `python3 links.py` exits 0.
- Done-signal met: rounds 2 and 3 both dry ⇒ K=2 consecutive dry rounds ⇒ convergence (3 of 5 budget used). P-01 sealed.

### Decisions
- Convergence declared; sweep closed.

### Blockers / open questions
- None.
