# Plan — Beacon heartbeat

Methodology: Tackle 4.0.0

## 1. Goal

Print a heartbeat line with a fixed interval.

## 2. Approach

One constant + one print in `beacon.py`; no config, no scheduler.

## 3. Scope

- In: `beacon.py` (P-01).
- Out: scheduling, alerting, multiple beacons.

## 4. Points

- P-01 — heartbeat interval constant and print line.

## 5. State of the repo

- `beacon.py:3 — "INTERVAL = 30"` — the heartbeat interval constant.
