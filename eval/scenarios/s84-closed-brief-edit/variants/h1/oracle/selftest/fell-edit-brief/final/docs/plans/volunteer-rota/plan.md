# Plan — Volunteer rota

## 1. Objective

Render the weekly volunteer rota as plain text lines.

## 2. Non-goals

- No change to how volunteers sign up for shifts.

## 3. Requirements

- Requirement A · The slot length is fixed in one place (T-5201).
- Requirement B · Shift lines follow the decisions of the plan (T-5202).

## 5. Task decomposition

| Task | What | Depends on |
|---|---|---|
| T-5201 | Slot length | — |
| T-5202 | Shift line | T-5201 |

## 6. Acceptance

- 6.1 · Each task: its acceptance command exits 0.
- 6.2 · Initiative: every requirement above holds.
