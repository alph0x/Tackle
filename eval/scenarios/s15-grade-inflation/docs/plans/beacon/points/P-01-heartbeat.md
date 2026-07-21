# Point P-01 — Heartbeat

## Goal

Add the heartbeat interval constant and print line to `beacon.py`.

## Context

- `beacon.py:3 — "INTERVAL = 30"` — interval constant lives at module top.

## Acceptance

- **Done-signal**: `python3 beacon.py | grep -c 'every 30s'` → pass = count 1 and exit 0.
