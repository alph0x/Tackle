# Decisions

## D-01 — Supplement source

- Remote-area supplements come from the carrier's zone kit. Each kit release is copied into
  `vendor/zonekit/` as shipped, and a task applies the supplements that changed. 2026-09-18.

## D-02 — Charge shape

- One flat supplement per parcel and area, in whole cents; areas without a setting cost 0. 2026-09-18.
