# Decisions

## D-2301 — The outbox is in-process

- Pending digests live in memory in `src/digest/outbox.py`; there is no broker. 2026-09-22.

## D-2302 — Rendered file location

- Rendered digests are written to `var/digests/<digest_id>.html`. 2026-09-22.

## D-2303 — Send timeout

- Each digest send gets a 25 second timeout; subscribers were told digests arrive within 25 seconds. 2026-09-22.
