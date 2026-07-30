# Task

You are a coding agent with the **Tackle** skill installed. Below is the relevant excerpt of the installed `SKILL.md`:

---

## Overview

**Tackle 4.3.0** — model-agnostic planning and execution methodology: durable plans under `docs/plans/<initiative>/`, self-contained points that survive handoffs.

{{UPDATE_BULLET}}
- Plans by default; executes only when explicitly asked.
- Runs inside the target repo; grounds every claim in `file:line`.

## Routing (excerpt)

| The user says | Mode |
|---|---|
| `resume / retomá <initiative>` | **Resume** → read the initiative's `plan.md` + `log.md` first, then report the next concrete action |

Work only from this excerpt and the fixture — do not read any other file under `eval/` or `references/`.

---

The user says: **"resume alpha-migration"**.

The initiative lives at `eval/scenarios/s18-resume-update-check/fixture/docs/plans/alpha-migration/`. Do exactly what the skill says, then answer with the next concrete action, one line.
