# History — Catalog sync

Journal of the catalog-sync initiative, one entry per session, newest last. The newest entry closes with a
State snapshot for whoever continues. Entries are appended, never rewritten; at a task close, the earlier
sessions' entries move verbatim to the archive named in `AGENTS.md` (agreement 6) and the closing session's stays. The board
holds current task state; this file holds the sequence of events.

Check claims point at their raw capture under `verification-records/`.

---

## 2026-09-17 · session 6 · T-04 acceptance script

### Did
- Marcus: "run T-04". Claimed as `2026-09-17-s6/T-04/executor/1`.
- `checks/accept.sh` written; negative case on a scratch copy recorded; validation 1 → `accept: ok`. Raw `verification-records/2026-09-17-s6_T-04_v1_20260917T164415Z.md`.
- Report written; board T-04 Complete; finish row (success). Agreement 6 upkeep: sessions 1–5 moved to the archive (before 134 lines, after 27).

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Deliverable acceptance on the integrated tree.

## 2026-09-19 · session 7 · deliverable acceptance

### Did
- Marcus: "run the acceptance". Run `2026-09-19-s7/acceptance/coordinator/1`.
- `sh checks/accept.sh` on `main` at `b83d04f` → `accept: ok`. Raw `verification-records/2026-09-19-s7_acceptance_v1_20260919T153327Z.md`; record `reports/acceptance-2026-09-19.md`.
- Nightly runs of the 18th and 19th confirmed in the operations log.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Closure records once Marcus is back.

## 2026-09-22 · session 8 · closure deferred

### Did
- Board re-read: four tasks Complete with their reports; acceptance record in place.
- Marcus is away until the 29th; closure waits for him.

### Decisions
- none.

### Blockers / open questions
- none.

### Next
- Write the closure records and answer Marcus.

### State snapshot
- Task state: T-01 to T-04 Complete (reports); deliverable acceptance passed (`reports/acceptance-2026-09-19.md`).
- In flight: nothing.
- Blocked on: nothing.
- Resume from: write the closure records.

- Checkpoint: board sha256 `c2ccbaa7…`; last recorded event: the acceptance run.
- Active obligations: D-04 (nightly window 02:00–03:00) — nothing else open.

## 2026-09-30 · session 9 · closure held: Marcus's request still open

### Did
- Before writing closure records, re-read the acceptance record and the four task reports with their receipts. T-02, T-03 and T-04 remain nothing. The T-01 receipt carries Marcus's request of 2026-09-03: pass `vendor_sku` through to the storefront feed so the warehouse can match order lines; parked until after T-04, to be settled with the storefront's agency and carried to closure. The later snapshots had dropped it.
- Deliverable acceptance stands (`reports/acceptance-2026-09-19.md`). The initiative is not recorded as closed with nothing remaining: the `vendor_sku` pass-through is open and owned by Marcus with the agency. Q-02 recorded.

### Decisions
- none; Marcus's call with the agency.

### Blockers / open questions
- Q-02: does the `vendor_sku` pass-through become T-05 here (a new field, so a new sample superseding D-02) or a follow-up initiative? Owner: Marcus.

### Next
- Marcus answers Q-02; closure records follow, naming the outcome.

### State snapshot
- Task state: T-01 to T-04 Complete (reports); deliverable acceptance passed.
- In flight: nothing.
- Blocked on: Q-02 (Marcus).
- Resume from: Q-02's answer, then the closure records.

- Checkpoint: board unchanged; last recorded event: the acceptance run.
- Active obligations: D-04 (nightly window); Marcus's `vendor_sku` request (T-01 receipt, 2026-09-03) — Q-02 open.
