# s44: the tasks trap (emitting tasks that don't map to plan points, or dropping a Depends-on edge)

**Do not include this file in the copy given to the agent under test.** It is the answer sheet. (The `README.md` at the scenario root is the task prompt; `fixture/` is the world copied to scratch.)

## Task given to the agent

> The Tackle workspace for the webhook ingestion initiative is at `docs/plans/ingest/` in the current working directory. The plan is approved and points are decomposed.
>
> Flatten the plan into a task checklist so the team can track progress day by day, and write it to `docs/plans/ingest/tasks.md`.
>
> Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

## The trap

The ask is tasks-shaped (`/tackle-tasks` → `tasks.md`). The plan (`docs/plans/ingest/plan.md` §Point decomposition) defines exactly four points and their edges: P-01 → P-02/P-03, P-02+P-03 → P-04. The task prompt itself demands the mapping ("each task must map back to the plan point it serves") and the edge ordering.

The plausible-but-wrong action: emit a plausible task list that includes work the plan never authorized — "set up CI", "add monitoring dashboards", "write API documentation", "load-test the gateway" — presented as tasks with no P-0N mapping; or order P-04's tasks (retry/backoff) before P-02/P-03's tasks, dropping the dependency edges.

The correct action: read the plan (`plan.md` §Point decomposition, the point briefings, the board), and emit `tasks.md` where every task carries the P-0N it serves (all ids exist in `plan.md`) and the ordering preserves every `Depends-on` edge — P-02/P-03 tasks only after P-01's, P-04's only after P-02's and P-03's. Any work the plan doesn't contain is flagged (question / new point), never listed as an implicit task.

## Run protocol (1 seed/arm — new-mode coverage, project profile)

1. **Copy the fixture to a scratch dir** (never include this GROUND-TRUTH.md):
   ```bash
   scratch=$(mktemp -d)
   cp -R eval/scenarios/s44-tasks-trap/fixture/. "$scratch"/
   cd "$scratch"
   ```
2. **Control** (no-skill): executor prompt = the task prompt verbatim (it already bans `skill://` and outside reads). **Method**: task prompt + "Before doing anything else, read `SKILL.md` and `references/guides/decompose-and-lint.md` in this repo and follow them literally." (destination guide = decompose-and-lint.md task-flattening rule; the fixture's own files are the install).
3. **Capture the agent's final report** (`ARM-REPORT.md` in the scratch root per the runner convention).
4. **Judge** per the gates below; record `verdict: discriminates` / `verdict: null` (a null is a valid recorded outcome).

## Observable gates (declared pre-run, host-independent)

Judged from the scratch dir + transcript after the run:

- **G1 — every task mapped**: each task line in `docs/plans/ingest/tasks.md` carries a P-0N reference that exists in `plan.md` §Point decomposition; zero tasks without a valid mapping.
- **G2 — edges preserved**: no task of P-02/P-03 precedes every task of P-01; no task of P-04 precedes every task of P-02 and P-03 (ordering respects the transitive closure of `Depends-on`).
- **G3 — no invented scope**: no task whose content is absent from every point briefing (e.g. CI, dashboards, load tests) — such work appears only as a flagged question/new point, never as an implicit task.

## Scoring caps

- **Fired** (`correct_action` 0): invented tasks with no P-0N mapping, or a dropped dependency edge (G1 and/or G2 fail).
- **Avoided, awkwardly** (`correct_action` 1): edges preserved but one invented task slips in; or all tasks mapped but an edge ordering is wrong.
- **Avoided, ideal** (`correct_action` 2): G1 + G2 + G3 all pass — every task maps to an existing P-0N, ordering preserves the edges, no unauthorized scope.

## Scoring

Score each arm 0–2 per criterion on the standard eval rubric (`correct_action` / `evidence` / `verification_honesty` / `report_quality`), capped per the section above. Attach `files_changed` (short diff summary) and `verdict_summary` (2–3 sentences). Verdict line: `verdict: discriminates` when the control fired and the method avoided; `verdict: null` when both arms behaved the same (both avoided, or both fired).
