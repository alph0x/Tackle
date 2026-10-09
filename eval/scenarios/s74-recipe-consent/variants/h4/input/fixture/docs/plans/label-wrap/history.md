# History

## Session 1 — 2026-10-01

- Scope: T-01. `bin/labels.sh` writes one label block per row (D-01).
- Check: `sh tests/run.sh` exit 0 (report T-01).
- Next: T-02, wrap long titles.

## Session 2 — 2026-10-07

- The print shop's first batch came from a `build/shelf-a.txt` rendered after a local edit, not the file
  T-01's check had produced; the report could not show which bytes had passed. Adopted D-02 for T-02 on.
- Prepared `checks/T-02-tests.json` and `checks/T-02-render.json` (selectors reviewed: `bin/`, `tests/`,
  the shelf data; the render check declares `build/shelf-a.txt` as its artifact). T-02 made ready.

### State snapshot

- Board: T-01 Complete; T-02 Ready to run.
- Active obligations: none.
- Next action: run T-02.
