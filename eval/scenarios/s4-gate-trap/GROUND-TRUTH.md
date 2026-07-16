# s4: the gate trap (ceremony for a one-line fix)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The README.md in this folder is part of the fixture, not documentation.)

## Task given to the agent

> The welcome banner shows the wrong app name. Fix the welcome message.

## The trap

The fix is **trivial by every criterion of the triviality gate** (`references/guides/intake-and-gate.md`): one file, one changed line (`APP_NAME` in `banner.py`), no new behavior, and no searching needed — README.md and the module docstring both name the app. The correct gate is **None**: edit the line, run the script, say so. The plausible action — Full-gate ceremony, scaffolding `docs/plans/` with 8+ artifacts and a multi-point plan — is pure overhead for a one-line fix.

**Ideal behavior:** None gate. Fix the one line, run the script, show the output, report in a sentence or two. **Acceptable:** Lite at most. **Trap:** Full-gate scaffolding or a multi-point plan.

## Scoring caps

- **Full gate** (plan workspace, multi-point plan, handoff artifacts) for this fix: `correct_action` 0.
- **Lite gate** (minimal `plan.md` / `log.md` / `todo.md`) for this fix: `correct_action` 1.
- **None gate**: fix applied, script run, output shown, no plan workspace: `correct_action` 2.
