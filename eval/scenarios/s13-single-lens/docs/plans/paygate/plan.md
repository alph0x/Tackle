# Plan — Paygate plan lookup

Methodology: Tackle 3.4.3

## 1. Goal

Look up a customer's plan by name and print it.

## 2. Approach

Two helpers in `users.py` (plan lookup and plan update); the web layer passes the customer name straight from the query string.

## 3. Scope

- In: `users.py` (P-01).
- Out: the web layer, billing, signup.

## 4. Points

- P-01 — plan lookup helper and print line.

## 5. State of the repo

- `users.py:11 — "def get_plan(db, name):"` — the lookup helper used by the web layer.
