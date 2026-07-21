# P-03 — README fare list refresh

Traces to: plan §1 · Depends on: P-02 · Touches: `README.md`

## Goal (single responsibility)

`README.md` line 3 lists the weekend fare alongside adult and child: `Adult: $9.50 · Child: $4.75 · Weekend: $12.00`.

## Context

- `README.md:3 — "Adult: $9.50"` — printed fare list, mirrors the constants.

## Done-signal

- `grep -c 'Weekend: \$12.00' README.md` → 1.

## Acceptance

- [ ] Done-signal output pasted in `log.md`.
