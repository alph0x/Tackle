# History archive — Catalog sync

Entries moved verbatim out of `history.md` under agreement 6 of `AGENTS.md`, oldest first; nothing here
changes after the move.

Moves: 2026-09-17 (session 6) — sessions 1–5, 107 lines.

---

## 2026-08-31 · session 1 · plan kickoff

### Intake (context gathered)
- Requirement: Marcus Oyelaran (operations, Larkspur Mercantile): "the storefront should take its items from the warehouse catalog export every night; Dana re-keys it every Monday and the stock is wrong by Wednesday."
- Docs read: the storefront agency's feed schema and sample (four fields, integer cents); the warehouse export (`product_id,title,price_cents,stock,vendor_sku`, written nightly at 01:30); `README.md` of shopfront-sync.
- Scope hints: the storefront's schema is fixed by the agency; the export shape is the warehouse's; the build runs on the operations host.
- Codebase: `~/shopfront-sync`, Python 3.10, `unittest`; no CI.
- Harness: Claude Code in the terminal; no model list, no telemetry, so the model map records `unknown` for `fast` and `frontier` and the session's own model for `standard`.

### Did
- Sizing: four tasks with an owner review of the reader — a Coordinated workspace at `docs/plans/catalog-sync/`.
- D-01 (gitignore) recorded with Marcus; core files scaffolded; `AGENTS.md` filled.
- Objective and exclusions drafted (R01–R04).

### Decisions
- D-01.

### Blockers / open questions
- Q-01: prices as cents or decimals? Marcus to confirm with the agency.

### Next
- Resolve Q-01, compile the briefs, run readiness.

### State snapshot
- Task state: nothing started.
- Active obligations: Q-01.

## 2026-09-01 · session 2 · readiness

### Did
- Q-01 resolved (integer cents); D-02 (the sample) and D-03 recorded; `tests/fixtures/expected-feed.json` placed as the sample.
- Four briefs compiled; chain T-01 → T-02 → T-03 → T-04 in `plan.md` §5; T-01 set Ready to run.
- Lint: 16 of 16 rows pass; ledger created with the v2 header.

### Decisions
- D-02, D-03.

### Blockers / open questions
- none.

### Next
- Run T-01 with Marcus reviewing the rows.

### State snapshot
- Task state: T-01 Ready to run; the rest Draft.
- Active obligations: none.

## 2026-09-03 · session 3 · T-01 and the owner's review

### Did
- Marcus: "run T-01". Claimed as `2026-09-03-s3/T-01/executor/1`.
- `tests/test_catalog.py` first, then `sync/catalog.py`. Validation 1 → exit 0. Raw `verification-records/2026-09-03-s3_T-01_v1_20260903T160712Z.md`.
- Review with Marcus over the rows: columns confirmed. He asked for the vendor's SKU to reach the storefront feed too, so the warehouse can match order lines without the lookup sheet. The storefront's sample (D-02) has no such field, so it is written into the T-01 receipt as remaining, to be settled with the agency after T-04.
- Report written with its receipt; board T-01 Complete; finish row (success, zero attempts). T-02 set Ready to run.

### Decisions
- none.

### Blockers / open questions
- Marcus's SKU pass-through request: parked, owner Marcus with the agency, carried to closure (T-01 receipt).

### Next
- T-02.

### State snapshot
- Task state: T-01 Complete; T-02 Ready to run; T-03, T-04 Draft.
- Active obligations: Marcus's SKU pass-through request (T-01 receipt), parked until after T-04.

## 2026-09-08 · session 4 · T-02

### Did
- Marcus: "run T-02". Claimed as `2026-09-08-s4/T-02/executor/1`.
- `tests/test_feed.py` first, then `sync/feed.py` and `sync/__main__.py`. Validation 1 → exit 0. Raw `verification-records/2026-09-08-s4_T-02_v1_20260908T172240Z.md`.
- Report written with its receipt; board T-02 Complete; finish row (success). T-03 set Ready to run.

### Decisions
- none.

### Blockers / open questions
- none new.

### Next
- T-03.

### State snapshot
- Task state: T-01, T-02 Complete; T-03 Ready to run; T-04 Draft.
- Active obligations: Marcus's SKU pass-through request (T-01 receipt), parked.

## 2026-09-12 · session 5 · T-03

### Did
- Marcus: "run T-03". Claimed as `2026-09-12-s5/T-03/executor/1`.
- `tools/nightly.sh` written; D-04 (window) recorded; cron entry installed by Marcus. Validation 1 → exit 0. Raw `verification-records/2026-09-12-s5_T-03_v1_20260912T151058Z.md`.
- Report written with its receipt; board T-03 Complete; finish row (success). T-04 set Ready to run.

### Decisions
- D-04.

### Blockers / open questions
- none new.

### Next
- T-04.

### State snapshot
- Task state: T-01 to T-03 Complete; T-04 Ready to run.
- Active obligations: D-04 (window); Marcus's SKU pass-through request (T-01 receipt), parked.
