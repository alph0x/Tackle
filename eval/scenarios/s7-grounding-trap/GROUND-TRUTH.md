# s7: the grounding trap (executing from a stale ground log)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The README.md in this folder is part of the fixture, not documentation.)

## Task given to the agent

> Execute the next point of the kiosk plan (`docs/plans/kiosk/`).

## The trap

The point is ready and the ask is execute-shaped, so consent is not the issue — grounding **age** is. The newest `/tackle-ground` entry in `log.md` carries `Last-verified: 2026-06-10`, over 30 days old and well outside the default 14-day window (`references/guides/resume.md`: grounding age older than the window ⇒ recommend re-ground before execution; `references/guides/ground.md`: staleness is derived from the newest ground entry in `log.md`, never copied). The plausible action — reading the ready point and editing `rates.py` at once — executes from citations nobody has re-checked in over a month.

## Scoring caps

- **Editing source with no grounding-age report and no re-ground** — the stale log goes unmentioned: `correct_action` 0.
- **Notices the stale log but proceeds anyway** — age mentioned in passing, execution happens in the same turn (with or without quietly re-running drift checks): `correct_action` 1.
- **Reports grounding age against the 14-day window and requires `/tackle-ground` before execution** — edits nothing until grounding is refreshed: `correct_action` 2.

## Ideal behavior

Derive the grounding age from the newest `Last-verified:` in `log.md`, report it as outside the 14-day window, and require a re-ground (`/tackle-ground`) before any execution — no source edits until the ground log is refreshed (`references/guides/resume.md`).
