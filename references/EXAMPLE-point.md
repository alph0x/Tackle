# Point P-02 — Cursor-based pagination on the items list endpoint

<!-- FILLED EXAMPLE (generic, illustrative). Shows what a good, self-contained, loop-runnable
     point looks like. Not part of any real plan — copy the SHAPE, not the contents. -->

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone. Links are for depth, not prerequisites — EXCEPT a named
> `design-contract.md` section the point implements, which IS required reading (this example
> has none, so the file truly stands alone). Tackle plans this point; it does not implement it here.

## Status & wiring
**Depends on**: P-01 (its `meta` envelope field — `reference.md` §Envelope) · execution status in `plan.md` §5. Runs in parallel with P-03 (disjoint Touches) — read off the graph, not re-listed.
- **Touches (write scope)**: `src/data/ItemsRepository.ts`, `src/api/ItemsController.ts`, `src/api/dto/ListResponse.ts`, `test/items/*`. Nothing else.

## Goal (single responsibility — one loop-completable change)
`GET /items` returns at most 50 items plus an opaque `nextCursor`; passing `?cursor=` returns
the next page deterministically under concurrent inserts. "Done" = a request loop over the
cursor visits every item exactly once. (One responsibility: keyset pagination — no filters, no sort change.)

## Context (grounded)
- `src/api/ItemsController.ts:34-58` — current handler returns the full list (no limit), `findAll()`.
- `src/data/ItemsRepository.ts:80` — `findAll()` does `ORDER BY created_at` only; no keyset support.
- `src/api/dto/ListResponse.ts:12` — response envelope; `meta` field added in P-01 (see `reference.md` §Envelope).
- Shared facts (envelope shape, error format): `reference.md` §Envelope, §Errors.

## Non-goals
- Offset/limit pagination (rejected — unstable under inserts; see `decisions.md` D-04).
- Changing the sort key or adding filters (separate point).

## Recommended approach
1. Add keyset query to `ItemsRepository`: `findPage(after: Cursor, limit)` ordering by `(created_at, id)`.
2. Encode the cursor as base64 of `(created_at,id)`; decode + validate in the controller.
3. Return `meta.nextCursor` (null on last page) in the existing envelope.
4. Tests: page boundary, last page (`nextCursor == null`), insert-during-pagination stability, malformed cursor → 400.

## Alternatives / fallbacks
- **If the table lacks a stable secondary sort key** → tie-break on `id`; if `id` isn't monotonic, fall back to `(created_at, pk)` and note it in `reference.md`.
- **If P-01's `meta` isn't merged yet** → put `nextCursor` at the top level temporarily and flag Q-07; don't block.

## Recommended starting prompt
```text
Resolve Point P-02 (cursor-based pagination on GET /items) of the "items-api" plan.
Repo: <repo path>. Read points/P-02-pagination.md first; it is self-contained.
Do: add keyset findPage() to ItemsRepository, base64 opaque cursor, expose meta.nextCursor.
Constraints: touch only ItemsRepository/ItemsController/ListResponse + test/items; don't change sort key or add filters; offset pagination is rejected (D-04).
Acceptance: a cursor loop visits every item exactly once, stable under concurrent inserts.
Loop until green: npm test -- test/items
```

## Acceptance — the loop's exit gate
- **Done-signal**: `npm test -- test/items` → pass = exit 0, all `test/items/*` green, 0 failures. Plus `grep -rn "findAll" src/api/ItemsController.ts` returns nothing (old unbounded path gone).
- [ ] Meets the **universal per-point acceptance** in `plan.md` §6.1 (don't restate it here).
- [ ] **Security** (endpoint axis) — folded into the done-signal: `test/items` asserts `GET /items` rejects unauthenticated and cross-tenant access (401/403), and that the cursor is opaque (base64 over `(created_at,id)` only — no internal PK or row count leaked).
- [ ] `GET /items` caps at 50 and returns `meta.nextCursor` (null on last page) — tested.
- [ ] Cursor loop visits every item exactly once under concurrent inserts — integration test asserts no dupes/skips across an insert.
- [ ] Every malformed-cursor shape → `400` not `500`: empty, non-base64, truncated, wrong field count — table-driven, suite asserts exactly 4 cases.
- **If it fails →** insert-stability flaky → sort key not deterministic, add `id` tie-break (see Alternatives); malformed-cursor 500s → decode/validate before the query, map to 400 at the boundary. Self-correct up to the workspace budget (`AGENTS.md`), then STOP + escalate.

## Open questions for this point
- Q-07 — does P-01's envelope land before this point? (non-blocking; fallback above)

## Definition of Ready (the gates that can FAIL)
- [x] Single responsibility — one change (keyset pagination), no "and".
- [x] No unresolved user-owned questions inside it (Q-07 non-blocking with a fallback).
- [x] Loop-ready — runnable done-signal (`npm test -- test/items`) with unambiguous pass (asserts the 4 cursor cases).
- [x] Cold-agent-resolvable from this file alone.
