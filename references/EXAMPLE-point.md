# Point P-02 — Cursor-based pagination on the items list endpoint

<!-- FILLED EXAMPLE (generic, illustrative). Shows what a good, self-contained point looks
     like. Not part of any real plan — copy the SHAPE, not the contents. -->

> **Self-contained briefing.** A fresh agent in a new session must be able to resolve THIS
> point from this file alone (links below are for depth, not prerequisites). Tackle plans
> this point; it does not implement it here.

## Status
**Depends on**: P-01 (response envelope must expose a `meta` object) · execution status tracked in `plan.md` §5.

## Goal
`GET /items` returns at most 50 items plus an opaque `nextCursor`; passing `?cursor=` returns
the next page deterministically under concurrent inserts. "Done" = a request loop over the
cursor visits every item exactly once.

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
Constraints: don't change sort key or add filters; offset pagination is rejected (D-04).
Acceptance: a cursor loop visits every item exactly once, stable under concurrent inserts.
Verify with: unit tests for boundary, last page, insert-stability, malformed cursor → 400.
```

## Acceptance criteria
- [ ] `GET /items` caps at 50 and returns `meta.nextCursor`.
- [ ] Cursor loop visits every item once under concurrent inserts.
- [ ] Malformed cursor → `400`, not `500`.

## Verification
- Unit tests on `ItemsRepository.findPage` + controller; integration test for the cursor loop.

## Open questions for this point
- Q-07 — does P-01's envelope land before this point? (non-blocking; fallback above)

## Definition of Ready (self-check before marking the briefing ready)
- [x] Goal is observable/testable.
- [x] Context is grounded in `file:line`, verified against the repo.
- [x] Recommended approach is concrete; alternatives/fallbacks cover the likely failure.
- [x] Starting prompt is pasteable and bounded — works on any model.
- [x] Acceptance + verification are stated.
- [x] Dependencies and open questions are linked.
- [x] A cold agent could resolve this point from this file alone.
