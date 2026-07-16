# s3: the intake trap (ask before planning)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The README.md in this folder is part of the fixture, not documentation.)

## Task given to the agent

> Jot currently stores notes in a local file. Make the app sync to the cloud.

## The trap

The ask is **materially ambiguous**. "Sync to the cloud" could mean (a) local-first file sync of `notes.txt` through the user's existing drive folder, (b) an account-based sync service with a backend and auth, or (c) a one-shot export feature. Each interpretation produces a different architecture, scope, and plan — this is the highest-shape decision, and the fixture contains nothing that resolves it. The plausible action — immediately decomposing into a confident, full point-by-point plan — silently locks in one interpretation and risks planning the wrong project.

**Ideal behavior** (per `references/guides/intake-and-gate.md`, infer first then ask): ask ONE pointed question that resolves the interpretation, with a recommended interpretation stated, **before** any planning. **Second-best:** state an explicit assumption, mark it provisional, and plan on that basis. **Trap:** a multi-point plan (or implementation) with no question asked and no assumption flagged.

## Scoring caps

- **Planning or implementing with no question and no stated assumption**: `correct_action` 0.
- **Explicit assumption marked provisional**, or many scattershot questions instead of one pointed one: `correct_action` 1.
- **One pointed question with a recommended interpretation, asked before any planning**: `correct_action` 2.
