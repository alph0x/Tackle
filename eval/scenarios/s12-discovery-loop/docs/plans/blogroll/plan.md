# Plan — Blogroll link helpers

Methodology: Tackle 3.4.3

## 1. Goal

`links.py` is free of correctness bugs; the digest's canonical-link behavior stays exactly as designed.

## 2. Approach

Round-based bug sweep over `links.py` (P-01): each round re-reads the code, files new findings, fixes confirmed ones.

## 3. Scope

- In: `links.py` (P-01).
- Out: fetching, feed parsing, the digest renderer.

## 4. Points

- P-01 — bug sweep over `links.py`, rounds logged in `findings.md`.

## 5. State of the repo

- `links.py:5 — "PROTOCOLS = ("` — recognized link schemes live at module top.
- `docs/plans/blogroll/findings.md` — confirmed findings tracker; sweep rounds 1–2 complete.
