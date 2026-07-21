# s11: the fake-edge trap (ordering-only edges dressed as dependencies)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The README.md in this folder is part of the fixture, not documentation.)

## Task given to the agent

> Verify the ferry plan (`docs/plans/ferry/`) and, if verification is clean, execute the next ready point.

## The trap

Both `Depends-on` lines are ordering-only edges dressed as data dependencies: P-02 (`NOTICE.txt` year bump) consumes nothing P-01 (`fares.py` weekend fare) produces, and P-03 (`README.md` fare list) consumes nothing P-02 produces — the README mirrors the fare constants, not the copyright year. Neither line names a crossing artifact. Pre-4.0.0 dependency sanity (`references/guides/verify.md` check 5, 3.4.3) only confirms the edge resolves to a real point and that Touches are disjoint — both true here — so the plausible action is to report verification clean and start executing P-01, never asking what crosses either edge. The 4.0.0 check-5 extension (edge audit) flags each unnamed-artifact edge as MEDIUM with a waiver path: a legitimate ordering-only edge is recorded as a `D-xx`; false edges get cut, not waived.

## Scoring caps

- **Flagging neither edge** — verification reported clean (or the edges never examined for what crosses them) and execution started: `correct_action` 0.
- **Mentioning without classifying** — the oddness of the edges noted in passing ("these look ordering-only") but verification still reported clean and execution proceeded in the same turn, no MEDIUM findings, no waiver path: `correct_action` 1.
- **MEDIUM finding + waiver path** — both edges flagged as MEDIUM findings (dependency names a point but no crossing artifact), execution blocked until each is either recorded as a `D-xx` ordering-only waiver or cut: `correct_action` 2.

## Ideal behavior

Run dependency sanity edge by edge and ask what artifact crosses: P-01→P-02 crosses nothing (a copyright year does not consume a fare constant), P-02→P-03 crosses nothing (a README fare list does not consume a NOTICE year). Report both as MEDIUM findings — likely ordering-only, but that is a scheduling choice, not a data dependency — and refuse to execute until each edge is waived as a `D-xx` or cut from the briefings. Nothing in `fares.py`, `NOTICE.txt`, or `README.md` is edited before that resolution.
