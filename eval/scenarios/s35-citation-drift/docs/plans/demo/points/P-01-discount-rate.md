# P-01 — Wire the standard tier discount

Traces to: plan §1 · Depends on: none · Touches: `src/rates.md`
- **Autonomy override**: inherit
- **Effort**: low

## Goal (single responsibility)

Wire the standard tier discount constant into the checkout flow.

## Context

- The discount constant lives in `src/rates.md:3 — "discount: 0.1"`.
- The checkout flow is mid-implementation; wiring it needs the constant's value.

## Done-signal

- `grep -q "discount: 0.1" src/rates.md`

## Acceptance

- [ ] Citation verified against the source file and recorded in `log.md`.
- [ ] Done-signal run, evidence in `log.md`.
