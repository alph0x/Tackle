# AGENTS — invoice reminder planning

This directory is a planning project. Plans live under `docs/plans/<name>/`, each with its own
`AGENTS.md`. The code the plans change sits beside them in `reminders/` (Python, standard library only) with tests in `tests/`.
Whether a plan's tasks are ready is settled as that plan's own `AGENTS.md` says under Validation.

Acceptance validator: python3 tools/brief_gate.py
