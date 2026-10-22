# Review 1 — shift line (T-5202)

Reviewer: the owner's walkthrough of the kiosk output, 2026-09-19. Three findings; none applied yet.

## Finding A (high) — early hours lose their leading zero

`rota/render.py` writes a nine o'clock start as `9:00`. The kiosk sorts the lines as text, so `9:00` lands after
`10:00`. Times must be `09:00`.

## Finding B (low) — T-5201's contract names a constant that is not there

The T-5201 brief says the contract is `rota.slots.SLOT_MINUTE`. The module defines `SLOT_MINUTES` (the T-5201
report names that one). The name in the brief points at nothing.

## Finding C (medium) — shift ends ignore the slot length

The end time adds a fixed sixty minutes per slot. A slot is the length in `rota.slots`, so a three-slot shift
shows an end time that is wrong by an hour and a half.
